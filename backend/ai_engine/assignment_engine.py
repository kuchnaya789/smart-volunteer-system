from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from aicte.aicte_calculator import compute_task_points
from ai_engine.eswam_model import compute_eswam, compute_location_distance_km
from ai_engine.fairness import compute_pool_fairness
from ai_engine.tie_breaker import resolve_tie
from ml.predictor import predict_success
from utils.normalization import extract_lat_lng, normalize


def _clamp01(x: Any) -> float:
    try:
        v = float(x)
    except Exception:
        v = 0.0
    return max(0.0, min(1.0, v))


def _finite_distance_km(val: Any) -> Optional[float]:
    try:
        v = float(val)
    except Exception:
        return None
    if not math.isfinite(v):
        return None
    return round(v, 2)


def _distance_norm_km(distance_km: float) -> float:
    if distance_km is None or distance_km != distance_km:  # NaN
        return 1.0
    if distance_km == float("inf"):
        return 1.0
    d = max(0.0, min(100.0, float(distance_km)))
    return d / 100.0


def _build_ml_features(
    eswam_breakdown: Dict[str, Any],
    volunteer: Dict[str, Any],
    task: Dict[str, Any],
    fairness: float,
    dist_km: float,
    dist_norm: float,
    workload_norm: float,
) -> Dict[str, float]:
    """
    Build richer feature vector compatible with the advanced Random Forest,
    while staying robust if some fields are missing.
    """
    skill_match = _clamp01(eswam_breakdown.get("skill_match"))
    willingness = _clamp01(eswam_breakdown.get("willingness", volunteer.get("willingness")))
    availability_norm = _clamp01(eswam_breakdown.get("availability", volunteer.get("availability")))
    availability_hours = availability_norm * 40.0

    # Urgency: prefer raw 1–10 scale if present, else from normalized urgency.
    if "urgency_raw" in task:
        urgency_level = float(task.get("urgency_raw") or 0.0)
    else:
        urgency_level = float(task.get("urgency", 0.0) or 0.0) * 10.0
    urgency_level = max(1.0, min(10.0, urgency_level))
    urgency_score = (urgency_level / 10.0) * 2.0  # map to approx [0,2] then normalized internally

    fairness_score = _clamp01(fairness)

    hours_required = float(task.get("hours_required", 0.0) or 0.0)
    time_compatibility = 1.0 if availability_hours >= hours_required else 0.5

    # Simple difficulty proxy based on hours.
    if hours_required <= 4:
        task_difficulty = 1.0
    elif hours_required <= 8:
        task_difficulty = 2.0
    elif hours_required <= 12:
        task_difficulty = 3.0
    elif hours_required <= 20:
        task_difficulty = 4.0
    else:
        task_difficulty = 5.0

    # Default NGO reputation and volunteer reliability; can be enhanced later when data is available.
    ngo_reputation = float(task.get("ngo_reputation_score", 4.0) or 4.0)
    volunteer_reliability = float(volunteer.get("reliability_score", 0.8) or 0.8)
    volunteer_aicte_points = max(0.0, float(volunteer.get("aicte_points", 0.0) or 0.0))
    # Normalize cumulative points (cap at 1000 for stability)
    volunteer_aicte_norm = normalize(volunteer_aicte_points, 1000.0)
    if task.get("total_points_possible") is not None:
        task_points_opportunity = max(0.0, float(task.get("total_points_possible") or 0.0))
    else:
        task_points_opportunity = max(0.0, float(compute_task_points(task).get("total_possible_points") or 0.0))
    task_points_norm = normalize(task_points_opportunity, 200.0)
    reliability_score = _clamp01(volunteer.get("reliability_score", volunteer_reliability))

    distance_km = max(0.0, float(dist_km if dist_km == dist_km else 0.0))
    distance_score = max(0.0, 1.0 - (distance_km / 50.0))

    return {
        "skill_match_ratio": skill_match,
        "willingness_score": willingness,
        "availability_hours": availability_hours,
        "distance_km": distance_km,
        "distance_score": distance_score,
        "urgency_level": urgency_level,
        "urgency_score": urgency_score,
        "fairness_score": fairness_score,
        "volunteer_reliability": volunteer_reliability,
        "time_compatibility": time_compatibility,
        "task_difficulty": task_difficulty,
        "ngo_reputation": ngo_reputation,
        "volunteer_aicte_points": volunteer_aicte_points,
        "volunteer_aicte_norm": volunteer_aicte_norm,
        "task_points_opportunity": task_points_opportunity,
        "task_points_norm": task_points_norm,
        "task_points_possible": task_points_opportunity,
        "reliability_score": reliability_score,
        # Legacy compatibility fields:
        "skill_match": skill_match,
        "availability": availability_norm,
        "distance_norm": _clamp01(dist_norm),
        "workload_norm": _clamp01(workload_norm),
    }


def run_assignment(task: Dict, volunteers: List[Dict]) -> Dict[str, Any]:
    """
    Master orchestrator:
    - Compute fairness for all volunteers
    - Compute location score for each volunteer vs task
    - Compute ESWAM score for each
    - Get ML prediction for each using richer feature vector
      (skill match, willingness, availability hours, distance, urgency, fairness, etc.)
    - Final score = 0.7 * ESWAM + 0.3 * ML_probability
    - Sort descending, handle ties with resolve_tie()
    - Return: assigned_volunteer, score_breakdown, all_scores list
    """
    pool_fairness = compute_pool_fairness(volunteers)

    # For workload_norm and AICTE normalization, gather pool maxima.
    tasks_done_list = []
    aicte_points_list = []
    for v in volunteers:
        try:
            tasks_done_list.append(int(v.get("tasks_done", 0) or 0))
        except Exception:
            tasks_done_list.append(0)
        try:
            aicte_points_list.append(float(v.get("aicte_points", 0.0) or 0.0))
        except Exception:
            aicte_points_list.append(0.0)
    nmax = max(tasks_done_list) if tasks_done_list else 0
    aicte_max = max(aicte_points_list) if aicte_points_list else 0.0

    all_scores: List[Dict[str, Any]] = []

    for v in volunteers:
        vid = str(v.get("_id") or v.get("id") or v.get("user_id") or "")
        fairness = float(pool_fairness.get(vid, 1.0))

        # Location distance and normalization (same field resolution as ESWAM).
        v_lat, v_lng = extract_lat_lng(v)
        t_lat, t_lng = extract_lat_lng(task)
        dist_km = compute_location_distance_km(v_lat, v_lng, t_lat, t_lng)
        dist_norm = _distance_norm_km(dist_km)

        eswam_score, eswam_breakdown = compute_eswam(v, task, fairness_score=fairness)

        try:
            tasks_done = int(v.get("tasks_done", 0) or 0)
        except Exception:
            tasks_done = 0
        workload_norm = (tasks_done / (nmax + 1)) if nmax >= 0 else 0.0
        workload_norm = _clamp01(workload_norm)

        feature_mapping = _build_ml_features(
            eswam_breakdown=eswam_breakdown,
            volunteer=v,
            task=task,
            fairness=fairness,
            dist_km=dist_km,
            dist_norm=dist_norm,
            workload_norm=workload_norm,
        )
        ml_prob = float(predict_success(feature_mapping))

        exp_score = normalize(v.get("aicte_points", 0.0), max(aicte_max, 1.0))
        opp_score = normalize(task.get("total_points_possible", feature_mapping.get("task_points_possible", 0.0)), 200.0)
        reliability_score = _clamp01(v.get("reliability_score", 0.0))
        aicte_factor = 0.5 * exp_score + 0.3 * opp_score + 0.2 * reliability_score

        final_score = 0.6 * float(eswam_score) + 0.25 * ml_prob + 0.15 * aicte_factor

        candidate = {
            "volunteer_id": vid,
            "name": v.get("name") or v.get("full_name") or "",
            "email": v.get("email") or "",
            "availability": _clamp01(v.get("availability")),
            "tasks_done": tasks_done,
            "registered_time": v.get("registered_time") or v.get("created_at"),
            "location_distance_km": dist_km,
            **eswam_breakdown,
            "ml_success_probability": ml_prob,
            "aicte_factor": float(aicte_factor),
            "volunteer_aicte_points": float(v.get("aicte_points", 0.0) or 0.0),
            "task_points_possible": float(task.get("total_points_possible", feature_mapping.get("task_points_possible", 0.0)) or 0.0),
            "volunteer_experience_norm": float(exp_score),
            "task_opportunity_norm": float(opp_score),
            "volunteer_aicte_norm": float(feature_mapping.get("volunteer_aicte_norm", 0.0)),
            "task_points_norm": float(feature_mapping.get("task_points_norm", 0.0)),
            "reliability_score": reliability_score,
            "final_score": float(final_score),
        }
        all_scores.append(candidate)

    # Sort descending by final_score.
    all_scores.sort(key=lambda x: float(x.get("final_score", 0.0)), reverse=True)

    assigned_volunteer = None
    score_breakdown = None
    if all_scores:
        top_score = float(all_scores[0]["final_score"])
        tied = [c for c in all_scores if abs(float(c.get("final_score", 0.0)) - top_score) < 1e-12]
        if len(tied) > 1:
            best = resolve_tie(tied)
            # Move best to front deterministically.
            all_scores.sort(
                key=lambda x: (
                    0 if x.get("volunteer_id") == best.get("volunteer_id") else 1,
                    -float(x.get("final_score", 0.0)),
                )
            )

        best = all_scores[0]
        assigned_volunteer = {
            "_id": best.get("volunteer_id"),
            "name": best.get("name") or "",
            "email": best.get("email") or "",
        }

        score_breakdown = {
            "skill_match": _clamp01(best.get("skill_match")),
            "willingness": _clamp01(best.get("willingness")),
            "availability": _clamp01(best.get("availability")),
            "urgency_handled": _clamp01(best.get("urgency_handled")),
            "fairness": _clamp01(best.get("fairness")),
            "location_proximity": _clamp01(best.get("location_proximity")),
            "location_distance_km": _finite_distance_km(best.get("location_distance_km")),
            "eswam_score": float(best.get("eswam_score", 0.0)),
            "ml_success_probability": float(best.get("ml_success_probability", 0.0)),
            "aicte_factor": float(best.get("aicte_factor", 0.0)),
            "volunteer_aicte_points": float(best.get("volunteer_aicte_points", 0.0)),
            "task_points_possible": float(best.get("task_points_possible", 0.0)),
            "volunteer_experience_norm": float(best.get("volunteer_experience_norm", 0.0)),
            "task_opportunity_norm": float(best.get("task_opportunity_norm", 0.0)),
            "volunteer_aicte_norm": float(best.get("volunteer_aicte_norm", 0.0)),
            "task_points_norm": float(best.get("task_points_norm", 0.0)),
            "reliability_score": float(best.get("reliability_score", 0.0)),
            "final_score": float(best.get("final_score", 0.0)),
            "formula": "Final Score = 0.6 × ESWAM + 0.25 × ML_Probability + 0.15 × AICTE_Factor",
        }

    return {
        "assigned_volunteer": assigned_volunteer,
        "score_breakdown": score_breakdown,
        "all_scores": all_scores,
    }

