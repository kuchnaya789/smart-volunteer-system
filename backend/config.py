import hashlib
import os

from dotenv import load_dotenv

# Ensure we load the project-root `.env` even when running `python app.py`
# from inside `backend/`.
_here = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_here, os.pardir))
_env_path = os.path.join(_project_root, ".env")

load_dotenv(_env_path if os.path.exists(_env_path) else None)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/volunteer_db")
# HS256: use 32+ bytes. When unset, derive a stable dev secret (log in again after first run).
JWT_SECRET = (os.getenv("JWT_SECRET") or "").strip()
if not JWT_SECRET:
    JWT_SECRET = hashlib.sha256(b"smart-volunteer-default-jwt-material-v1").hexdigest()
PORT = int(os.getenv("PORT", 5000))
# Set in `.env` to enable POST /api/auth/register with role "admin" and matching admin_secret.
ADMIN_REGISTER_SECRET = (os.getenv("ADMIN_REGISTER_SECRET") or "").strip()

# Comma-separated list of allowed CORS origins for /api/*.
# Example:
# CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:5173
_cors_origins_env = (os.getenv("CORS_ORIGINS") or "").strip()
if _cors_origins_env:
    CORS_ORIGINS = [o.strip() for o in _cors_origins_env.split(",") if o.strip()]
else:
    CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]

