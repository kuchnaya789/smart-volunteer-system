from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId


def normalize_skills_field(skills: Any) -> List[str]:
    if skills is None:
        return []
    if isinstance(skills, list):
        return [str(s).strip() for s in skills if str(s).strip()]
    if isinstance(skills, str):
        return [p.strip() for p in skills.replace(";", ",").split(",") if p.strip()]
    return []


def _to_object_id(value: Any) -> Optional[ObjectId]:
    if value is None:
        return None
    if isinstance(value, ObjectId):
        return value
    try:
        return ObjectId(str(value))
    except Exception:
        return None


def serialize_user(user: Dict[str, Any]) -> Dict[str, Any]:
    if not user:
        return {}

    out = dict(user)
    if "_id" in out:
        out["_id"] = str(out["_id"])
    if "created_at" in out and isinstance(out["created_at"], datetime):
        out["created_at"] = out["created_at"].isoformat() + "Z"
    if "registered_time" in out and isinstance(out["registered_time"], datetime):
        out["registered_time"] = out["registered_time"].isoformat() + "Z"

    out.pop("password_hash", None)
    return out


def user_public_projection() -> Dict[str, int]:
    # Hide password hash by default
    return {"password_hash": 0}


def normalize_user_update(payload: Dict[str, Any]) -> Dict[str, Any]:
    # Keep only supported profile fields (student profile update).
    allowed = {
        "skills",
        "willingness",
        "availability",
        "location",
        "location_lat",
        "location_lng",
    }
    return {k: payload[k] for k in allowed if k in payload}


def ensure_user_indexes(users_collection) -> None:
    users_collection.create_index("email", unique=True)
    users_collection.create_index("role")


def get_user_id(value: Any) -> Optional[ObjectId]:
    return _to_object_id(value)

