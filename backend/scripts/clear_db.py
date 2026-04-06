"""
Drop all application collections (users, tasks, assignments, activities).
Run from repo root: python backend/scripts/clear_db.py
Or from backend: python scripts/clear_db.py
"""
from __future__ import annotations

import os
import sys

# Allow imports from backend when run as script
_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from database.db import (  # noqa: E402
    activities_collection,
    assignments_collection,
    tasks_collection,
    users_collection,
)


def main() -> None:
    users_collection.drop()
    tasks_collection.drop()
    assignments_collection.drop()
    activities_collection.drop()
    print("Dropped collections: users, tasks, assignments, activities.")


if __name__ == "__main__":
    main()
