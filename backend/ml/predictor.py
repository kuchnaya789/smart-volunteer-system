from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import joblib
import numpy as np
import pandas as pd

_model = None
_feature_columns: List[str] = []


def _load_advanced_or_basic_model() -> None:
    """
    Load advanced tuned model if available, else fall back to basic 4-feature model.
    Also loads feature column ordering for safe vector construction.
    """
    global _model, _feature_columns
    if _model is not None:
        return

    base_dir = Path(__file__).resolve().parent
    advanced_dir = base_dir / "advanced_outputs"
    advanced_model = advanced_dir / "swam_random_forest_model.pkl"
    advanced_features = advanced_dir / "model_features.pkl"

    if advanced_model.exists() and advanced_features.exists():
        _model = joblib.load(str(advanced_model))
        _feature_columns = joblib.load(str(advanced_features))
        return

    # Fallback: use basic 4-feature model when available.
    basic_model = base_dir / "random_forest.pkl"
    _feature_columns = ["skill_match", "availability", "distance_norm", "workload_norm"]
    if basic_model.exists():
        _model = joblib.load(str(basic_model))
    else:
        _model = None


def load_model() -> None:
    _load_advanced_or_basic_model()


def _vector_from_mapping(features: Dict[str, Any]) -> List[float]:
    """
    Build feature vector from a mapping using the learned feature ordering.
    Missing values default to 0.0 for safety.
    """
    if not _feature_columns:
        _load_advanced_or_basic_model()
    vec: List[float] = []
    for name in _feature_columns:
        value = features.get(name, 0.0)
        try:
            v = float(value)
        except Exception:
            v = 0.0
        vec.append(v)
    return vec


def _vector_from_sequence(seq: Sequence[float]) -> List[float]:
    """
    Backwards‑compatible path for callers that still pass a simple list.
    - If len matches feature_columns, use as‑is.
    - If len==4, treat as [skill_match, availability, distance_norm, workload_norm]
      and map into whatever features we have, defaulting others.
    """
    if not _feature_columns:
        _load_advanced_or_basic_model()

    if len(seq) == len(_feature_columns):
        return [float(x) for x in seq]

    if len(seq) == 4:
        skill, avail, dist_norm, workload = seq
        mapping = {
            "skill_match_ratio": skill,
            "skill_match": skill,
            "willingness_score": avail,
            "availability": avail,
            "availability_hours": float(avail) * 40.0,
            "distance_norm": dist_norm,
            "distance_km": max(0.0, (1.0 - float(dist_norm)) * 100.0),
            "distance_score": 1.0 - float(dist_norm),
            "workload_norm": workload,
            "task_points_possible": 0.0,
            "task_points_norm": 0.0,
            "volunteer_aicte_points": 0.0,
            "volunteer_aicte_norm": 0.0,
            "reliability_score": max(0.0, min(1.0, 1.0 - float(workload))),
        }
        return _vector_from_mapping(mapping)

    # Fallback: pad or truncate
    vec = [float(x) for x in seq]
    if len(vec) < len(_feature_columns):
        vec = vec + [0.0] * (len(_feature_columns) - len(vec))
    else:
        vec = vec[: len(_feature_columns)]
    return vec


def _heuristic_probability(features: Any) -> float:
    """
    Safe fallback for serverless environments when model artifacts are unavailable.
    """
    if isinstance(features, dict):
        skill = float(features.get("skill_match_ratio", features.get("skill_match", 0.0)) or 0.0)
        avail = float(features.get("willingness_score", features.get("availability", 0.0)) or 0.0)
        dist_score = float(
            features.get("distance_score", 1.0 - float(features.get("distance_norm", 1.0) or 1.0)) or 0.0
        )
        reliability = float(features.get("reliability_score", 0.5) or 0.5)
    else:
        seq = list(features) if isinstance(features, (list, tuple, np.ndarray)) else [0.0, 0.0, 1.0, 0.5]
        skill = float(seq[0]) if len(seq) > 0 else 0.0
        avail = float(seq[1]) if len(seq) > 1 else 0.0
        dist_score = 1.0 - (float(seq[2]) if len(seq) > 2 else 1.0)
        reliability = 1.0 - (float(seq[3]) if len(seq) > 3 else 0.5)

    prob = 0.45 * skill + 0.25 * avail + 0.2 * max(0.0, min(1.0, dist_score)) + 0.1 * max(
        0.0, min(1.0, reliability)
    )
    return max(0.0, min(1.0, prob))


def predict_success(features: Any) -> float:
    """
    predict_success(features) -> float probability 0-1

    - If `features` is a dict: interpreted as {feature_name: value}.
    - If list/tuple/array: treated as ordered feature vector (with backwards compatibility for 4-length list).
    """
    _load_advanced_or_basic_model()

    if isinstance(features, dict):
        vec = _vector_from_mapping(features)
    elif isinstance(features, (list, tuple, np.ndarray)):
        vec = _vector_from_sequence(features)
    else:
        raise TypeError("features must be dict or sequence of numbers")

    if _model is None:
        return _heuristic_probability(features)

    if hasattr(_model, "n_features_in_") and int(_model.n_features_in_) != len(vec):
        raise ValueError(
            f"Feature length mismatch: model expects {_model.n_features_in_} features, got {len(vec)}"
        )
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=".*does not have valid feature names.*",
            category=UserWarning,
        )
        x = pd.DataFrame([vec], columns=_feature_columns)
        proba = _model.predict_proba(x)[0]
    # Binary classifier: use positive class when present; else fall back to max index.
    if len(proba) > 1:
        prob = float(proba[1])
    else:
        prob = float(proba[0])
    if prob != prob or prob is None:  # NaN
        prob = 0.5
    if prob < 0.0:
        return 0.0
    if prob > 1.0:
        return 1.0
    return prob

