from __future__ import annotations

from datetime import datetime

from bson import ObjectId
from flask import Blueprint, jsonify, request

from aicte.aicte_calculator import calculate_aicte_score
from ai_engine.assignment_engine import run_assignment
from database.db import activities_collection, assignments_collection, tasks_collection, users_collection
from models.user_model import normalize_skills_field
from routes.auth_routes import token_required
from utils.normalization import extract_lat_lng

assignment_bp = Blueprint("assignments", __name__)


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


@assignment_bp.post("/run/<task_id>")
@token_required
def run_for_task(task_id: str):
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
    caller_id = ObjectId(request.user.get("user_id"))  # type: ignore[attr-defined]
    if role == "ngo" and task.get("ngo_id") != caller_id:
        return _json_error("Forbidden", 403)

    volunteers = list(users_collection.find({"role": "student"}))
    if not volunteers:
        return _json_error("No volunteers available", 400)

    result = run_assignment(task, volunteers)
    assigned = result.get("assigned_volunteer")
    if not assigned:
        return _json_error("Unable to assign volunteer", 400)

    assigned_oid = ObjectId(assigned["_id"])

    # Persist
    assignments_collection.insert_one(
        {
            "task_id": oid,
            "ngo_id": task.get("ngo_id"),
            "assigned_volunteer_id": assigned_oid,
            "score_breakdown": result.get("score_breakdown"),
            "all_scores": result.get("all_scores"),
            "created_at": datetime.utcnow(),
        }
    )

    tasks_collection.update_one(
        {"_id": oid},
        {
            "$set": {
                "assigned_volunteer_id": assigned_oid,
                "status": "assigned",
                "score_breakdown": result.get("score_breakdown"),
                "all_scores": result.get("all_scores"),
            }
        },
    )
    users_collection.update_one({"_id": assigned_oid}, {"$inc": {"tasks_assigned": 1}})

    volunteer_doc = users_collection.find_one({"_id": assigned_oid}, {"password_hash": 0})
    if volunteer_doc:
        volunteer_doc["_id"] = str(volunteer_doc["_id"])

    return jsonify(
        {
            "assigned_volunteer": volunteer_doc or assigned,
            "score_breakdown": result.get("score_breakdown"),
            "all_scores": result.get("all_scores"),
            "aicte_factor": (result.get("score_breakdown") or {}).get("aicte_factor"),
            "volunteer_aicte_points": (result.get("score_breakdown") or {}).get("volunteer_aicte_points"),
            "task_points_possible": (result.get("score_breakdown") or {}).get("task_points_possible"),
            "reliability_score": (result.get("score_breakdown") or {}).get("reliability_score"),
        }
    )


@assignment_bp.get("/my-assignments")
@token_required
def my_assignments():
    err = _require_role("student")
    if err:
        return err

    user_id = request.user.get("user_id")  # type: ignore[attr-defined]
    uid = ObjectId(user_id)

    user = users_collection.find_one({"_id": uid}, {"password_hash": 0}) or {}
    if user:
        user["_id"] = str(user["_id"])
        user["skills"] = normalize_skills_field(user.get("skills"))
        u_lat, u_lng = extract_lat_lng(user)
        if u_lat is not None and u_lng is not None:
            user["location_lat"] = u_lat
            user["location_lng"] = u_lng

    tasks = []
    for t in tasks_collection.find({"assigned_volunteer_id": uid}).sort("created_at", -1):
        t["_id"] = str(t["_id"])
        t["ngo_id"] = str(t["ngo_id"])
        if t.get("assigned_volunteer_id"):
            t["assigned_volunteer_id"] = str(t["assigned_volunteer_id"])
        tasks.append(t)

    activities = []
    for a in activities_collection.find({"$or": [{"volunteer_id": uid}, {"user_id": uid}]}).sort("created_at", -1):
        a["_id"] = str(a["_id"])
        if a.get("volunteer_id") is not None:
            a["volunteer_id"] = str(a["volunteer_id"])
        if a.get("user_id") is not None:
            a["user_id"] = str(a["user_id"])
        a["task_id"] = str(a["task_id"])
        activities.append(a)

    # Always compute from activity log for consistency, then sync user aggregate.
    aicte_calc = calculate_aicte_score(activities)
    total_points = float(aicte_calc.get("total_aicte_points", 0.0))
    users_collection.update_one({"_id": uid}, {"$set": {"aicte_points": total_points}})
    user["aicte_points"] = total_points

    return jsonify(
        {
            "user": user,
            "assigned_tasks": tasks,
            "activities": activities,
            "activities_breakdown": aicte_calc.get("breakdown", []),
            "total_aicte_points": total_points,
            "formula": "AICTE = Σ(Hi × Pi)",
            "aicte_formula": aicte_calc.get("formula"),
        }
    )


@assignment_bp.get("/ngo-assignments")
@token_required
def ngo_assignments():
    err = _require_roles("ngo", "admin")
    if err:
        return err

    role = request.user.get("role")  # type: ignore[attr-defined]
    if role == "admin":
        cursor = tasks_collection.find({}).sort("created_at", -1)
    else:
        ngo_id = request.user.get("user_id")  # type: ignore[attr-defined]
        nid = ObjectId(ngo_id)
        cursor = tasks_collection.find({"ngo_id": nid}).sort("created_at", -1)

    out = []
    for t in cursor:
        t["_id"] = str(t["_id"])
        t["ngo_id"] = str(t["ngo_id"])
        volunteer = None
        if t.get("assigned_volunteer_id"):
            volunteer = users_collection.find_one({"_id": t["assigned_volunteer_id"]}, {"password_hash": 0})
            if volunteer:
                volunteer["_id"] = str(volunteer["_id"])
            t["assigned_volunteer_id"] = str(t["assigned_volunteer_id"])

        ngo_summary = None
        if role == "admin":
            try:
                ngo_oid = ObjectId(t["ngo_id"])
            except Exception:
                ngo_oid = None
            if ngo_oid:
                ndoc = users_collection.find_one({"_id": ngo_oid}, {"password_hash": 0, "name": 1, "email": 1, "role": 1})
                if ndoc:
                    ngo_summary = {
                        "_id": str(ndoc["_id"]),
                        "name": ndoc.get("name") or "",
                        "email": ndoc.get("email") or "",
                        "role": ndoc.get("role") or "",
                    }

        t_lat, t_lng = extract_lat_lng(t)
        if t_lat is not None and t_lng is not None:
            t["location_lat"] = t_lat
            t["location_lng"] = t_lng
        if volunteer:
            v_lat, v_lng = extract_lat_lng(volunteer)
            if v_lat is not None and v_lng is not None:
                volunteer["location_lat"] = v_lat
                volunteer["location_lng"] = v_lng

        row = {
            "task": t,
            "assigned_volunteer": volunteer,
            "score_breakdown": t.get("score_breakdown"),
            "all_scores": t.get("all_scores") or [],
        }
        if ngo_summary is not None:
            row["ngo"] = ngo_summary
        out.append(row)

    return jsonify(out)

