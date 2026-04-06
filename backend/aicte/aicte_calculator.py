from __future__ import annotations

from typing import Any, Dict, List


ACTIVITY_TYPE_RATES = {
    "community_service": 2.0,
    "teaching": 3.0,
    "health_camp": 2.5,
    "disaster_relief": 4.0,
    "environment": 2.0,
    "skill_training": 3.0,
    "event_management": 2.0,
    "default": 2.0,
}


def compute_task_points(task: Dict[str, Any]) -> Dict[str, float]:
    activity_type = str(task.get("activity_type") or "default")
    default_pph = float(ACTIVITY_TYPE_RATES.get(activity_type, ACTIVITY_TYPE_RATES["default"]))
    pph = float(task.get("points_per_hour", default_pph) or default_pph)
    hours = float(task.get("hours_required", task.get("hours", 0.0)) or 0.0)
    return {
        "points_per_hour": pph,
        "total_possible_points": hours * pph,
    }


def calculate_aicte_score(activities: List[dict]) -> Dict[str, Any]:
    """
    IEEE paper formula: AICTE_Score = Σ(Hi * Pi)
    - Hi: hours
    - Pi: points per hour (activity type rate by default; if activity includes points_per_hour use that)
    """
    breakdown = []
    total = 0.0
    for a in activities or []:
        hours = float(a.get("hours", a.get("hours_required", 0)) or 0.0)
        activity_type = str(a.get("activity_type") or "default")
        pph = a.get("points_per_hour")
        if pph is None:
            pph = ACTIVITY_TYPE_RATES.get(activity_type, ACTIVITY_TYPE_RATES["default"])
        pph = float(pph or 0.0)
        points = hours * pph
        total += points
        breakdown.append(
            {
                "task_id": a.get("task_id"),
                "activity_type": activity_type,
                "hours": hours,
                "points_per_hour": pph,
                "points_earned": points,
                "points": points,  # backward compatibility
                "formula": f"{hours} × {pph}",
            }
        )

    return {
        "total_points": total,
        "total_aicte_points": total,
        "breakdown": breakdown,
        "formula": "AICTE = Σ(Hi × Pi)",
        "legacy_formula": "AICTE_Score = Σ(Hi * Pi)",
    }

