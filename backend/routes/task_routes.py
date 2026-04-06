from __future__ import annotations

from datetime import datetime

from bson import ObjectId
from flask import Blueprint, jsonify, request

from aicte.aicte_calculator import ACTIVITY_TYPE_RATES, calculate_aicte_score, compute_task_points
from database.db import activities_collection, assignments_collection, tasks_collection, users_collection
from routes.auth_routes import token_required
from utils.normalization import parse_json_numeric_coord

task_bp = Blueprint("tasks", __name__)


def _json_error(message: str, status: int = 400):
    return jsonify({"error": message}), status


def _require_role(role: str):
    if request.user.get("role") != role:  # type: ignore[attr-defined]
        return _json_error("Forbidden", 403)
    return None


def _require_roles(*roles: str):
    if request.user.get("role") not in roles:  # type: ignore[attr-defined]
        return _json_error("Forbidden", 403)
    return None


@task_bp.post("/")
@token_required
def create_task():
    role = request.user.get("role")  # type: ignore[attr-defined]
    payload = request.get_json(force=True, silent=True) or {}

    if role == "admin":
        raw_ngo = payload.get("ngo_id")
        if not raw_ngo:
            return _json_error("ngo_id is required when creating a task as admin", 400)
        try:
            ngo_oid = ObjectId(str(raw_ngo).strip())
        except Exception:
            return _json_error("Invalid ngo_id", 400)
        if not users_collection.find_one({"_id": ngo_oid, "role": "ngo"}):
            return _json_error("NGO not found", 404)
        ngo_id = str(ngo_oid)
    else:
        err = _require_role("ngo")
        if err:
            return err
        ngo_id = request.user.get("user_id")  # type: ignore[attr-defined]

    title = str(payload.get("title") or "").strip()
    description = str(payload.get("description") or "").strip()
    required_skills = payload.get("required_skills") or []
    if not isinstance(required_skills, list):
        return _json_error("required_skills must be a list")
    required_skills = [str(s).strip() for s in required_skills if str(s).strip()]
    if not required_skills:
        return _json_error("At least one required skill is required", 400)

    urgency_raw = float(payload.get("urgency", 0) or 0)
    urgency = max(0.0, min(1.0, urgency_raw / 10.0))

    location = str(payload.get("location") or "").strip()
    location_lat = parse_json_numeric_coord(payload.get("location_lat"))
    location_lng = parse_json_numeric_coord(payload.get("location_lng"))
    hours_required = float(payload.get("hours_required", 0) or 0)
    activity_type = str(payload.get("activity_type") or "community_service").strip()
    default_pph = float(ACTIVITY_TYPE_RATES.get(activity_type, ACTIVITY_TYPE_RATES["default"]))
    points_per_hour = float(payload.get("points_per_hour", default_pph) or default_pph)
    task_points = compute_task_points(
        {
            "activity_type": activity_type,
            "points_per_hour": points_per_hour,
            "hours_required": hours_required,
        }
    )

    if not title or not description or not location:
        return _json_error("title, description, location are required")

    doc = {
        "ngo_id": ObjectId(ngo_id),
        "title": title,
        "description": description,
        "required_skills": required_skills,
        "urgency": urgency,
        "urgency_raw": urgency_raw,
        "location": location,
        "location_lat": location_lat,
        "location_lng": location_lng,
        "hours_required": hours_required,
        "points_per_hour": task_points["points_per_hour"],
        "total_points_possible": task_points["total_possible_points"],
        "activity_type": activity_type,
        "status": "open",
        "assigned_volunteer_id": None,
        "created_at": datetime.utcnow(),
        "completed_at": None,
        "score_breakdown": None,
        "all_scores": None,
    }
    res = tasks_collection.insert_one(doc)
    doc["_id"] = str(res.inserted_id)
    doc["ngo_id"] = str(doc["ngo_id"])
    return jsonify(doc), 201


@task_bp.get("/")
@token_required
def list_tasks():
    role = request.user.get("role")  # type: ignore[attr-defined]
    user_id = request.user.get("user_id")  # type: ignore[attr-defined]

    if role == "admin":
        cursor = tasks_collection.find({}).sort("created_at", -1)
    elif role == "ngo":
        cursor = tasks_collection.find({"ngo_id": ObjectId(user_id)}).sort("created_at", -1)
    else:
        cursor = tasks_collection.find({"status": {"$in": ["open", "assigned", "completed"]}}).sort("created_at", -1)

    tasks = []
    for t in cursor:
        t["_id"] = str(t["_id"])
        t["ngo_id"] = str(t["ngo_id"])
        if t.get("assigned_volunteer_id"):
            t["assigned_volunteer_id"] = str(t["assigned_volunteer_id"])
        tasks.append(t)
    return jsonify(tasks)


@task_bp.get("/<task_id>")
@token_required
def task_detail(task_id: str):
    try:
        oid = ObjectId(task_id)
    except Exception:
        return _json_error("Invalid task id", 400)

    t = tasks_collection.find_one({"_id": oid})
    if not t:
        return _json_error("Task not found", 404)
    t["_id"] = str(t["_id"])
    t["ngo_id"] = str(t["ngo_id"])
    if t.get("assigned_volunteer_id"):
        t["assigned_volunteer_id"] = str(t["assigned_volunteer_id"])
    return jsonify(t)


@task_bp.delete("/<task_id>")
@token_required
def delete_task(task_id: str):
    err = _require_roles("ngo", "admin")
    if err:
        return err

    try:
        oid = ObjectId(task_id)
    except Exception:
        return _json_error("Invalid task id", 400)

    task = tasks_collection.find_one({"_id": oid})
    if not task:
        return _json_error("Task not found", 404)

    role = request.user.get("role")  # type: ignore[attr-defined]
    uid = ObjectId(request.user.get("user_id"))  # type: ignore[attr-defined]
    if role == "ngo" and task.get("ngo_id") != uid:
        return _json_error("Forbidden", 403)

    volunteer_id = task.get("assigned_volunteer_id")
    if volunteer_id:
        users_collection.update_one(
            {"_id": volunteer_id, "tasks_assigned": {"$gt": 0}},
            {"$inc": {"tasks_assigned": -1}},
        )

    assignments_collection.delete_many({"task_id": oid})
    activities_collection.delete_many({"task_id": oid})
    tasks_collection.delete_one({"_id": oid})
    return jsonify({"message": "Task deleted"})


@task_bp.put("/<task_id>/complete")
@token_required
def complete_task(task_id: str):
    err = _require_roles("ngo", "admin")
    if err:
        return err

    try:
        oid = ObjectId(task_id)
    except Exception:
        return _json_error("Invalid task id", 400)

    task = tasks_collection.find_one({"_id": oid})
    if not task:
        return _json_error("Task not found", 404)

    role = request.user.get("role")  # type: ignore[attr-defined]
    uid = ObjectId(request.user.get("user_id"))  # type: ignore[attr-defined]
    if role == "ngo" and task.get("ngo_id") != uid:
        return _json_error("Forbidden", 403)

    if (task.get("status") or "").lower() == "completed":
        return jsonify({"message": "Already completed"})

    volunteer_id = task.get("assigned_volunteer_id")
    if not volunteer_id:
        return _json_error("Task is not assigned to any volunteer", 400)

    hours = float(task.get("hours_required", 0) or 0)
    pph = float(task.get("points_per_hour", 2.0) or 2.0)
    activity_type = str(task.get("activity_type") or "community_service")

    aicte = calculate_aicte_score(
        [
            {
                "hours": hours,
                "points_per_hour": pph,
                "activity_type": activity_type,
                "task_title": task.get("title"),
            }
        ]
    )
    earned = float(aicte["total_aicte_points"])

    tasks_collection.update_one(
        {"_id": oid},
        {"$set": {"status": "completed", "completed_at": datetime.utcnow()}},
    )

    user_before = users_collection.find_one({"_id": volunteer_id}) or {}
    prev_done = int(user_before.get("tasks_done", 0) or 0)
    prev_assigned = int(user_before.get("tasks_assigned", 0) or 0)
    new_done = prev_done + 1
    reliability = new_done / (prev_assigned + 1)
    reliability = max(0.0, min(1.0, reliability))

    users_collection.update_one(
        {"_id": volunteer_id},
        {"$inc": {"aicte_points": earned, "tasks_done": 1}, "$set": {"reliability_score": reliability}},
    )

    activities_collection.insert_one(
        {
            "user_id": volunteer_id,
            "volunteer_id": volunteer_id,  # backward compatibility
            "task_id": oid,
            "task_title": task.get("title"),
            "hours": hours,
            "points_per_hour": pph,
            "points_earned": earned,
            "activity_type": activity_type,
            "created_at": datetime.utcnow(),
            "completed_at": datetime.utcnow(),
            "formula": aicte.get("formula"),
        }
    )

    return jsonify(
        {
            "message": "Task marked complete",
            "earned_points": earned,
            "aicte": aicte,
        }
    )

