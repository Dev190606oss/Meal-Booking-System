import os
from urllib.parse import urlparse, unquote
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "meal_booking_system_super_secret_key_2026")
    
    # Cloud environment detection (e.g. Render sets RENDER=true)
    IS_RENDER = os.getenv("RENDER", "").lower() in ("1", "true", "yes")

    # Database Configuration: Check for standard DATABASE_URL first
    _db_url = os.getenv("DATABASE_URL") or os.getenv("JAWSDB_URL") or os.getenv("CLEARDB_DATABASE_URL")
    if _db_url:
        _parsed = urlparse(_db_url)
        DB_USER = unquote(_parsed.username or "")
        DB_PASSWORD = unquote(_parsed.password or "")
        DB_HOST = _parsed.hostname or "127.0.0.1"
        DB_PORT = int(_parsed.port or 3306)
        DB_NAME = _parsed.path.lstrip("/") or "meal_booking_db"
    else:
        DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
        DB_PORT = int(os.getenv("DB_PORT", 3306))
        DB_USER = os.getenv("DB_USER", "root")
        DB_PASSWORD = os.getenv("DB_PASSWORD", "")
        DB_NAME = os.getenv("DB_NAME", "meal_booking_db")

    # SSL configuration for remote cloud MySQL instances
    DB_SSL = os.getenv("DB_SSL", "0").lower() in ("1", "true", "yes")

    # Server Configuration
    HOST = os.getenv("HOST", "0.0.0.0" if IS_RENDER else "127.0.0.1")
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")

    # Session & Cookie Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "1" if IS_RENDER else "0").lower() in ("1", "true", "yes")

    # Delivery & Fee Defaults
    DELIVERY_FEE = 40.00
    TAX_RATE_PCT = 5.0 # 5% GST on food services
