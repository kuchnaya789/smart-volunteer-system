from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from bson import ObjectId


def _to_object_id(value: Any) -> Optional[ObjectId]:
    if value is None:
        return None
    if isinstance(value, ObjectId):
        return value
    try:
        return ObjectId(str(value))
    except Exception:
        return None


def serialize_task(task: Dict[str, Any]) -> Dict[str, Any]:
    if not task:
        return {}

    out = dict(task)
    if "_id" in out:
        out["_id"] = str(out["_id"])
    if "ngo_id" in out:
        out["ngo_id"] = str(out["ngo_id"])
    if "assigned_volunteer_id" in out and out["assigned_volunteer_id"] is not None:
        out["assigned_volunteer_id"] = str(out["assigned_volunteer_id"])
    if "created_at" in out and isinstance(out["created_at"], datetime):
        out["created_at"] = out["created_at"].isoformat() + "Z"
    if "completed_at" in out and isinstance(out["completed_at"], datetime):
        out["completed_at"] = out["completed_at"].isoformat() + "Z"
    return out


def get_task_id(value: Any) -> Optional[ObjectId]:
    return _to_object_id(value)

