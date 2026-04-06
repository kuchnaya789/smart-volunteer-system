from __future__ import annotations

from datetime import datetime, timedelta
from functools import wraps

import jwt
from bson import ObjectId
from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from config import ADMIN_REGISTER_SECRET, JWT_SECRET
from database.db import users_collection
from models.user_model import normalize_skills_field
from utils.normalization import extract_lat_lng, parse_json_numeric_coord

auth_bp = Blueprint("auth", __name__)


def _json_error(message: str, status: int = 400):
    return jsonify({"error": message}), status


def _create_token(user_id: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(days=7),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def token_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return _json_error("Missing or invalid token", 401)
        token = auth_header.split(" ", 1)[1].strip()
        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except Exception:
            return _json_error("Invalid or expired token", 401)

        request.user = data  # type: ignore[attr-defined]
        return fn(*args, **kwargs)

    return wrapper


@auth_bp.post("/register")
def register():
    payload = request.get_json(force=True, silent=True) or {}
    role = str(payload.get("role") or "").strip().lower()
    if role not in {"student", "ngo", "admin"}:
        return _json_error('role must be "student", "ngo", or "admin"')

    if role == "admin":
        if not ADMIN_REGISTER_SECRET:
            return _json_error("Admin registration is disabled (set ADMIN_REGISTER_SECRET in .env)", 403)
        if str(payload.get("admin_secret") or "").strip() != ADMIN_REGISTER_SECRET:
            return _json_error("Invalid admin_secret", 403)

    email = str(payload.get("email") or "").strip().lower()
    password = str(payload.get("password") or "")
    name = str(payload.get("name") or payload.get("full_name") or payload.get("organization_name") or "").strip()
    if not email or not password or not name:
        return _json_error("name, email, password are required")

    if users_collection.find_one({"email": email}):
        return _json_error("Email already registered", 409)

    doc = {
        "role": role,
        "name": name,
        "email": email,
        "password_hash": generate_password_hash(password),
        "created_at": datetime.utcnow(),
        "registered_time": datetime.utcnow(),
        "skills": [],
        "willingness": 0.0,
        "availability": 0.0,
        "location": "",
        "location_lat": None,
        "location_lng": None,
        "tasks_done": 0,
        "tasks_assigned": 0,
        "aicte_points": 0.0,
        "reliability_score": 0.0,
    }
    if role == "ngo":
        doc["organization_type"] = str(payload.get("organization_type") or "").strip()

    res = users_collection.insert_one(doc)
    user_id = str(res.inserted_id)
    token = _create_token(user_id, role)
    return jsonify({"token": token, "user_id": user_id, "role": role, "name": name})


@auth_bp.post("/login")
def login():
    payload = request.get_json(force=True, silent=True) or {}
    email = str(payload.get("email") or "").strip().lower()
    password = str(payload.get("password") or "")
    if not email or not password:
        return _json_error("email and password are required")

    user = users_collection.find_one({"email": email})
    if not user or not check_password_hash(user.get("password_hash", ""), password):
        return _json_error("Invalid credentials", 401)

    user_id = str(user["_id"])
    role = str(user.get("role") or "")
    token = _create_token(user_id, role)
    return jsonify({"token": token, "user_id": user_id, "role": role, "name": user.get("name")})


@auth_bp.put("/profile")
@token_required
def update_profile():
    user_id = request.user.get("user_id")  # type: ignore[attr-defined]
    role = request.user.get("role")  # type: ignore[attr-defined]
    if role != "student":
        return _json_error("Student only", 403)

    payload = request.get_json(force=True, silent=True) or {}

    skills = payload.get("skills", [])
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.replace(";", ",").split(",") if s.strip()]
    elif not isinstance(skills, list):
        return _json_error("skills must be a list or comma-separated string")
    skills = [str(s).strip() for s in skills if str(s).strip()]

    willingness_raw = float(payload.get("willingness", 0) or 0)
    willingness = max(0.0, min(1.0, willingness_raw / 10.0))

    availability_raw = float(payload.get("availability", 0) or 0)
    availability = max(0.0, min(1.0, availability_raw / 40.0))

    location = str(payload.get("location") or "").strip()
    location_lat = parse_json_numeric_coord(payload.get("location_lat"))
    location_lng = parse_json_numeric_coord(payload.get("location_lng"))

    update = {
        "skills": skills,
        "willingness": willingness,
        "availability": availability,
        "location": location,
        "location_lat": location_lat,
        "location_lng": location_lng,
    }

    users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": update})
    user = users_collection.find_one({"_id": ObjectId(user_id)}, {"password_hash": 0})
    if user:
        user["_id"] = str(user["_id"])
        user["skills"] = normalize_skills_field(user.get("skills"))
        u_lat, u_lng = extract_lat_lng(user)
        if u_lat is not None and u_lng is not None:
            user["location_lat"] = u_lat
            user["location_lng"] = u_lng
    return jsonify({"message": "Profile updated", "user": user})

