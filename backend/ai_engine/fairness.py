from __future__ import annotations

from typing import Dict, Iterable, List


def compute_fairness_score(tasks_done: int, nmax: int) -> float:
    """
    IEEE paper formula:
    F(v) = 1 - (Nv / (Nmax + 1))
    """
    try:
        nv = max(0, int(tasks_done))
    except Exception:
        nv = 0
    try:
        nmax_i = max(0, int(nmax))
    except Exception:
        nmax_i = 0

    return 1.0 - (nv / (nmax_i + 1))


def compute_pool_fairness(volunteers: List[dict]) -> Dict[str, float]:
    """
    Returns: {volunteer_id: fairness_score}
    Uses tasks_done field on volunteer docs.
    """
    tasks = []
    for v in volunteers:
        try:
            tasks.append(int(v.get("tasks_done", 0) or 0))
        except Exception:
            tasks.append(0)
    nmax = max(tasks) if tasks else 0

    scores: Dict[str, float] = {}
    for v in volunteers:
        vid = str(v.get("_id") or v.get("id") or v.get("user_id") or "")
        scores[vid] = float(compute_fairness_score(v.get("tasks_done", 0) or 0, nmax))
    return scores

