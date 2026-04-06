from __future__ import annotations

from pymongo import MongoClient

from config import MONGO_URI


def _get_db_name_from_uri(uri: str) -> str | None:
    # mongodb://host:port/dbname?...
    try:
        tail = uri.split("://", 1)[1]
        path = tail.split("/", 1)[1] if "/" in tail else ""
        if not path:
            return None
        db_part = path.split("?", 1)[0].strip()
        return db_part or None
    except Exception:
        return None


client = MongoClient(MONGO_URI)

try:
    db = client.get_default_database()
except Exception:
    db = None

if db is None:
    db_name = _get_db_name_from_uri(MONGO_URI) or "volunteer_db"
    db = client[db_name]

users_collection = db["users"]
tasks_collection = db["tasks"]
assignments_collection = db["assignments"]
activities_collection = db["activities"]


def initialize_database() -> None:
    # Indexes only — no seed data or bulk field backfills (data comes from your registrations and API calls).
    users_collection.create_index("email", unique=True)
    users_collection.create_index("role")
    tasks_collection.create_index("ngo_id")
    tasks_collection.create_index("status")
    assignments_collection.create_index("task_id")
    activities_collection.create_index("volunteer_id")

