import os
import sys
from app import create_app
from app.config import Config
from app.db import test_db_connection

app = create_app()

def print_startup_banner(host, port, debug, db_status):
    print("=" * 65)
    print("  Meal Booking System - Smart Discovery & Booking Platform")
    print("  DBMS College Project | Python, Flask & MySQL")
    print("=" * 65)
    print(f"  Web Server:      http://{host}:{port}")
    print(f"  Debug Mode:      {'Enabled' if debug else 'Disabled'}")
    print(f"  Database Host:   {Config.DB_HOST}:{Config.DB_PORT}")
    print(f"  Database User:   {Config.DB_USER}")
    print(f"  Database Name:   {Config.DB_NAME}")
    print("-" * 65)

    if db_status["connected"] and db_status["database_exists"]:
        print(f"  [OK] Database Connected ({db_status['table_count']} relational tables ready)")
        print("  Customer Demo:   email: rahul.sharma@example.com | pass: password123")
        print("  Admin Demo:      email: admin@mealbooking.com   | pass: password123")
    else:
        print("  [!] WARNING: DATABASE CONNECTION OR SCHEMA ISSUE DETECTED")
        if db_status.get("error"):
            print(f"  Error: {db_status['error']}")
        print("\n  Troubleshooting Steps:")
        for step in db_status.get("troubleshooting", []):
            print(f"    * {step}")
        print("\n  Tip: Run 'python database/init_db.py' to initialize the database.")
    print("=" * 65)


if __name__ == "__main__":
    host = Config.HOST
    port = Config.PORT
    debug = Config.DEBUG

    # Run non-destructive database health check
    db_status = test_db_connection()
    print_startup_banner(host, port, debug, db_status)

    app.run(host=host, port=port, debug=debug)
