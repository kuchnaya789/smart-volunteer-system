from __future__ import annotations

from bson import ObjectId
from flask import Blueprint, jsonify, request

from database.db import activities_collection, assignments_collection, tasks_collection, users_collection
from routes.auth_routes import token_required

admin_bp = Blueprint("admin", __name__)


def _json_error(message: str, status: int = 400):
    return jsonify({"error": message}), status


def _require_admin():
    if request.user.get("role") != "admin":  # type: ignore[attr-defined]
        return _json_error("Forbidden", 403)
    return None


def _serialize_user(doc: dict) -> dict:
    out = dict(doc)
    out.pop("password_hash", None)
    out["_id"] = str(out["_id"])
    return out


@admin_bp.get("/users")
@token_required
def list_users():
    if err := _require_admin():
        return err

    role_filter = (request.args.get("role") or "").strip().lower()
    q: dict = {}
    if role_filter in {"student", "ngo", "admin"}:
        q["role"] = role_filter

    users = []
    for u in users_collection.find(q).sort("created_at", -1):
        users.append(_serialize_user(u))
    return jsonify(users)


@admin_bp.delete("/users/<user_id>")
@token_required
def delete_user(user_id: str):
    if err := _require_admin():
        return err

    if user_id == request.user.get("user_id"):  # type: ignore[attr-defined]
        return _json_error("Cannot delete your own admin account", 400)

    try:
        oid = ObjectId(user_id)
    except Exception:
        return _json_error("Invalid user id", 400)

    user_doc = users_collection.find_one({"_id": oid})
    if not user_doc:
        return _json_error("User not found", 404)

    role = str(user_doc.get("role") or "")

    if role == "ngo":
        task_ids = [t["_id"] for t in tasks_collection.find({"ngo_id": oid}, {"_id": 1})]
        if task_ids:
            assignments_collection.delete_many({"task_id": {"$in": task_ids}})
            activities_collection.delete_many({"task_id": {"$in": task_ids}})
            tasks_collection.delete_many({"_id": {"$in": task_ids}})
    elif role == "student":
        tasks_collection.update_many(
            {"assigned_volunteer_id": oid},
            {
                "$set": {
                    "assigned_volunteer_id": None,
                    "status": "open",
                    "score_breakdown": None,
                    "all_scores": None,
                }
            },
        )
        assignments_collection.delete_many({"assigned_volunteer_id": oid})
        activities_collection.delete_many({"$or": [{"volunteer_id": oid}, {"user_id": oid}]})

    users_collection.delete_one({"_id": oid})
    return jsonify({"message": "User deleted", "deleted_id": user_id})


@admin_bp.get("/stats")
@token_required
def stats():
    if err := _require_admin():
        return err
    return jsonify(
        {
            "users_total": users_collection.count_documents({}),
            "students": users_collection.count_documents({"role": "student"}),
            "ngos": users_collection.count_documents({"role": "ngo"}),
            "admins": users_collection.count_documents({"role": "admin"}),
            "tasks": tasks_collection.count_documents({}),
            "assignments": assignments_collection.count_documents({}),
        }
    )
