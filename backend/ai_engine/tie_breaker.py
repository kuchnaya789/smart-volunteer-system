from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


def _as_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        try:
            return datetime.utcfromtimestamp(float(value))
        except Exception:
            return datetime.max
    if isinstance(value, str):
        # Best-effort ISO parsing
        try:
            v = value.replace("Z", "+00:00")
            return datetime.fromisoformat(v)
        except Exception:
            return datetime.max
    return datetime.max


def resolve_tie(tied_volunteers: List[Dict]) -> Dict:
    """
    IEEE paper deterministic tie-breaking when ESWAM scores are equal:
    1) Higher availability (desc)
    2) Fewer tasks_done (asc)
    3) Shorter location_distance_km (asc)
    4) Earlier registered_time (asc)
    """
    if not tied_volunteers:
        return {}

    def key(v: Dict) -> Tuple:
        availability = float(v.get("availability", 0.0) or 0.0)
        tasks_done = int(v.get("tasks_done", 0) or 0)
        dist = float(v.get("location_distance_km", float("inf")) or float("inf"))
        registered = _as_dt(v.get("registered_time") or v.get("created_at") or v.get("registeredAt"))
        return (-availability, tasks_done, dist, registered)

    return sorted(tied_volunteers, key=key)[0]

