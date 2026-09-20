import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "meal_booking_system_super_secret_key_2026")
    
    # Database Configuration
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", 3307))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "meal_booking_db")

    # Delivery & Fee Defaults
    DELIVERY_FEE = 40.00
    TAX_RATE_PCT = 5.0 # 5% GST on food services
