from __future__ import annotations

import math
from typing import Dict, Iterable, List, Optional, Set, Tuple

from utils.normalization import extract_lat_lng, is_valid_lat_lon, parse_optional_coord


DEFAULT_WEIGHTS = {
    "skill": 0.25,
    "willingness": 0.20,
    "availability": 0.20,
    "urgency": 0.15,
    "fairness": 0.10,
    "location": 0.10,
}


def _skill_token_set(values: Optional[Iterable[str] | str]) -> Set[str]:
    """
    Flatten skills: list entries can contain commas; strings split by comma/semicolon.
    """
    if values is None:
        return set()
    if isinstance(values, str):
        items: List[str] = [values]
    else:
        try:
            items = [str(x) for x in values if x is not None]
        except TypeError:
            return set()
    out: Set[str] = set()
    for item in items:
        for p in item.replace(";", ",").split(","):
            t = p.strip().lower()
            if t:
                out.add(t)
    return out


def _task_required_ordered(values: Optional[Iterable[str] | str]) -> List[str]:
    """Unique required skills in order (comma-split per list element)."""
    if values is None:
        return []
    if isinstance(values, str):
        items = [values]
    else:
        items = [str(x) for x in values if x is not None]
    seen: Set[str] = set()
    ordered: List[str] = []
    for item in items:
        for p in item.replace(";", ",").split(","):
            t = p.strip().lower()
            if t and t not in seen:
                seen.add(t)
                ordered.append(t)
    return ordered


def _volunteer_covers_required(vol_tokens: Set[str], required: str) -> bool:
    """Exact token match or substring match (min length 3) either way."""
    r = required.strip().lower()
    if not r or not vol_tokens:
        return False
    if r in vol_tokens:
        return True
    if len(r) < 3:
        return False
    for v in vol_tokens:
        if len(v) < 3:
            if v == r:
                return True
            continue
        if r in v or v in r:
            return True
    return False


def skill_coverage_ratio(volunteer_skills: Optional[Iterable[str] | str], task_required: Optional[Iterable[str] | str]) -> float:
    """
    Fraction of required task skills satisfied (order preserved, unique requirements).
    Example: 1 of 2 required matched → 0.5. Uses case-insensitive tokens; commas
    inside one list item count as multiple skills; allows partial word overlap for len≥3.
    """
    vs = _skill_token_set(volunteer_skills)
    reqs = _task_required_ordered(task_required)
    if not reqs:
        return 0.0
    if not vs:
        return 0.0
    matched = sum(1 for r in reqs if _volunteer_covers_required(vs, r))
    return max(0.0, min(1.0, float(matched) / float(len(reqs))))


def jaccard_similarity(a: Optional[Iterable[str] | str], b: Optional[Iterable[str] | str]) -> float:
    sa = _skill_token_set(a)
    sb = _skill_token_set(b)
    if not sa and not sb:
        return 0.0
    inter = len(sa.intersection(sb))
    union = len(sa.union(sb))
    return inter / union if union else 0.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def _location_proximity_haversine_km(v_lat: float, v_lng: float, t_lat: float, t_lng: float) -> Tuple[float, float]:
    """Return (proximity 0–1, great-circle distance km). Clamped to 0–100 km for score."""
    d = float(haversine_km(float(v_lat), float(v_lng), float(t_lat), float(t_lng)))
    if math.isnan(d) or math.isinf(d):
        return 0.0, float("nan")
    d_clamped = min(max(d, 0.0), 100.0)
    prox = max(0.0, min(1.0, 1.0 - d_clamped / 100.0))
    return prox, d


def compute_location_distance_km(v_lat, v_lng, t_lat, t_lng) -> float:
    a = parse_optional_coord(v_lat)
    b = parse_optional_coord(v_lng)
    c = parse_optional_coord(t_lat)
    d = parse_optional_coord(t_lng)
    if a is None or b is None or c is None or d is None:
        return float("inf")
    try:
        return float(haversine_km(a, b, c, d))
    except Exception:
        return float("inf")


def compute_eswam(
    volunteer: Dict,
    task: Dict,
    fairness_score: float,
    weights: Optional[Dict[str, float]] = None,
) -> Tuple[float, Dict[str, float]]:
    """
    Implement EXACT IEEE paper formula:
    ESWAM(v,t) = ws*S(v,t) + ww*W(v) + wa*A(v,t) + wu*U(t) + wf*F(v) + wl*L(v,t)
    """
    w = dict(DEFAULT_WEIGHTS)
    if weights:
        w.update(weights)

    skill_match = skill_coverage_ratio(volunteer.get("skills"), task.get("required_skills"))
    willingness = float(volunteer.get("willingness", 0.0) or 0.0)
    availability = float(volunteer.get("availability", 0.0) or 0.0)
    urgency = float(task.get("urgency", 0.0) or 0.0)

    v_lat, v_lng = extract_lat_lng(volunteer)
    t_lat, t_lng = extract_lat_lng(task)
    location_proximity = 0.5
    location_distance_km: Optional[float] = None
    if is_valid_lat_lon(v_lat, v_lng) and is_valid_lat_lon(t_lat, t_lng):
        prox, dist_km = _location_proximity_haversine_km(v_lat, v_lng, t_lat, t_lng)
        if not math.isnan(dist_km):
            location_proximity = prox
            location_distance_km = dist_km

    fairness = max(0.0, min(1.0, float(fairness_score)))

    eswam = (
        w["skill"] * skill_match
        + w["willingness"] * willingness
        + w["availability"] * availability
        + w["urgency"] * urgency
        + w["fairness"] * fairness
        + w["location"] * location_proximity
    )

    breakdown = {
        "skill_match": max(0.0, min(1.0, float(skill_match))),
        "willingness": max(0.0, min(1.0, float(willingness))),
        "availability": max(0.0, min(1.0, float(availability))),
        "urgency_handled": max(0.0, min(1.0, float(urgency))),
        "fairness": fairness,
        "location_proximity": max(0.0, min(1.0, float(location_proximity))),
        "location_distance_km": location_distance_km,
        "eswam_score": float(eswam),
    }
    return float(eswam), breakdown
