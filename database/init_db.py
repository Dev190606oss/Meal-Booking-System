"""
Meal Booking System - Database Initialization and Health Check Script
======================================================================
This CLI utility safely sets up, seeds, verifies, or resets the MySQL database
for the Meal Booking System.

Execution Order:
  1. schema.sql      - Database creation, tables, foreign keys, constraints
  2. seed.sql        - Realistic initial Pune restaurants, meals, offers, bookings
  3. views.sql       - Analytical reporting views
  4. triggers.sql    - Business logic triggers (booking totals, meal availability)
  5. procedures.sql  - Stored procedures for dashboard & reporting

Usage:
  python database/init_db.py            # Safe initialization (prompts if tables exist)
  python database/init_db.py --check    # Non-destructive database health & schema check
  python database/init_db.py --reset    # Force drop and recreate all tables/views/routines
  python database/init_db.py --seed-only # Run seed.sql without modifying schema
  python database/init_db.py --skip-seed # Setup schema, views, triggers without seed data
  python database/init_db.py --force    # Skip confirmation prompt for reset
"""

import os
import sys
import re
import argparse
import pymysql
import pymysql.cursors
from dotenv import load_dotenv

# Ensure root directory is in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.config import Config

DB_HOST = Config.DB_HOST
DB_PORT = Config.DB_PORT
DB_USER = Config.DB_USER
DB_PASSWORD = Config.DB_PASSWORD
DB_NAME = Config.DB_NAME
DB_SSL = Config.DB_SSL

EXPECTED_TABLES = [
    "Customer", "Restaurant", "Meal", "Offer", "Staff",
    "Booking", "Booking_Item", "Payment", "Feedback"
]
EXPECTED_VIEWS = [
    "v_booking_summary", "v_customer_stats", "v_popular_meals", "v_restaurant_summary"
]
EXPECTED_TRIGGERS = [
    "trg_prevent_unavailable_meal",
    "trg_update_meal_rating_after_feedback",
    "trg_update_restaurant_rating_after_feedback"
]
EXPECTED_PROCEDURES = [
    "sp_get_admin_dashboard_stats",
    "sp_get_restaurant_analytics",
    "sp_get_customer_profile_stats",
    "sp_validate_offer"
]


def get_raw_connection(include_database=True):
    """Establish a PyMySQL connection with or without specifying the target database."""
    kwargs = {
        "host": DB_HOST,
        "port": DB_PORT,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "database": DB_NAME if include_database else None,
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": True
    }
    if DB_SSL:
        kwargs["ssl"] = {"ssl_mode": "REQUIRED", "check_hostname": False}
    return pymysql.connect(**kwargs)


def parse_sql_file(filepath):
    """
    Parse an SQL file into executable statement blocks.
    Accurately supports MySQL DELIMITER commands (e.g., DELIMITER $$ ... DELIMITER ;)
    used in triggers and stored procedures.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"SQL file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    statements = []
    current_delimiter = ";"
    buffer = []

    for line in content.splitlines():
        trimmed = line.strip()

        # Check for DELIMITER change
        delim_match = re.match(r"^DELIMITER\s+(\S+)$", trimmed, re.IGNORECASE)
        if delim_match:
            # If there is leftover buffer, flush it first
            stmt = "\n".join(buffer).strip()
            if stmt:
                statements.append(stmt)
                buffer = []
            current_delimiter = delim_match.group(1)
            continue

        # Add line to current statement buffer
        buffer.append(line)

        # Check if the line ends with current delimiter (ignoring trailing single-line comments)
        line_clean = re.sub(r"--.*$", "", trimmed).strip()
        if line_clean.endswith(current_delimiter):
            full_stmt = "\n".join(buffer).strip()

            # Remove the active delimiter from the end of statement
            if current_delimiter != ";":
                delim_pos = full_stmt.rfind(current_delimiter)
                if delim_pos != -1:
                    full_stmt = (full_stmt[:delim_pos] + full_stmt[delim_pos + len(current_delimiter):]).strip()
            else:
                delim_pos = full_stmt.rfind(";")
                if delim_pos != -1:
                    full_stmt = full_stmt[:delim_pos].strip()

            # Verify statement contains executable SQL after removing comments
            clean_check = re.sub(r"--.*$", "", full_stmt, flags=re.MULTILINE)
            clean_check = re.sub(r"/\*.*?\*/", "", clean_check, flags=re.DOTALL).strip()

            if clean_check:
                statements.append(full_stmt)
            buffer = []

    # Final buffer flush if any
    final_stmt = "\n".join(buffer).strip()
    if final_stmt:
        if current_delimiter != ";":
            delim_pos = final_stmt.rfind(current_delimiter)
            if delim_pos != -1:
                final_stmt = (final_stmt[:delim_pos] + final_stmt[delim_pos + len(current_delimiter):]).strip()
        else:
            delim_pos = final_stmt.rfind(";")
            if delim_pos != -1:
                final_stmt = final_stmt[:delim_pos].strip()

        clean_check = re.sub(r"--.*$", "", final_stmt, flags=re.MULTILINE)
        clean_check = re.sub(r"/\*.*?\*/", "", clean_check, flags=re.DOTALL).strip()
        if clean_check:
            statements.append(final_stmt)

    return statements


def execute_sql_file(conn, filepath):
    """Execute all statements in an SQL script using the active connection."""
    filename = os.path.basename(filepath)
    statements = parse_sql_file(filepath)
    executed_count = 0

    with conn.cursor() as cursor:
        for idx, stmt in enumerate(statements, 1):
            try:
                cursor.execute(stmt)
                executed_count += 1
            except Exception as e:
                snippet = stmt[:120].replace("\n", " ")
                raise RuntimeError(
                    f"Error executing statement #{idx} in {filename}: {e}\nQuery snippet: {snippet}..."
                ) from e

    return executed_count


def check_database():
    """
    Inspect the MySQL server and database schema.
    Returns a dictionary of health check metrics.
    """
    result = {
        "connected": False,
        "database_exists": False,
        "tables": [],
        "views": [],
        "triggers": [],
        "procedures": [],
        "record_counts": {},
        "errors": []
    }

    # 1. Test Server Connection
    try:
        conn = get_raw_connection(include_database=False)
    except Exception as e:
        result["errors"].append(f"Cannot connect to MySQL server at {DB_HOST}:{DB_PORT} as '{DB_USER}': {e}")
        return result

    result["connected"] = True

    try:
        with conn.cursor() as cur:
            # Check if target database exists
            cur.execute("SHOW DATABASES LIKE %s", (DB_NAME,))
            if not cur.fetchone():
                result["errors"].append(f"Database '{DB_NAME}' does not exist.")
                return result

            result["database_exists"] = True
            cur.execute(f"USE `{DB_NAME}`")

            # Get Tables (BASE TABLE)
            cur.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = %s AND table_type = 'BASE TABLE'",
                (DB_NAME,)
            )
            result["tables"] = sorted([row.get("TABLE_NAME") or row.get("table_name") for row in cur.fetchall()])

            # Get Views
            cur.execute(
                "SELECT table_name FROM information_schema.views WHERE table_schema = %s",
                (DB_NAME,)
            )
            result["views"] = sorted([row.get("TABLE_NAME") or row.get("table_name") for row in cur.fetchall()])

            # Get Triggers
            cur.execute(
                "SELECT trigger_name FROM information_schema.triggers WHERE trigger_schema = %s",
                (DB_NAME,)
            )
            result["triggers"] = sorted([row.get("TRIGGER_NAME") or row.get("trigger_name") for row in cur.fetchall()])

            # Get Stored Procedures
            cur.execute(
                "SELECT routine_name FROM information_schema.routines WHERE routine_schema = %s AND routine_type = 'PROCEDURE'",
                (DB_NAME,)
            )
            result["procedures"] = sorted([row.get("ROUTINE_NAME") or row.get("routine_name") for row in cur.fetchall()])

            # Record counts for existing tables
            for tbl in result["tables"]:
                try:
                    cur.execute(f"SELECT COUNT(*) AS cnt FROM `{tbl}`")
                    row = cur.fetchone()
                    result["record_counts"][tbl] = row["cnt"]
                except Exception:
                    result["record_counts"][tbl] = "N/A"

    finally:
        conn.close()

    return result


def print_check_report(report):
    """Print a clean, user-friendly diagnostic report of database health."""
    print("=" * 65)
    print(" MEAL BOOKING SYSTEM - DATABASE HEALTH CHECK")
    print("=" * 65)
    print(f" Target Host:     {DB_HOST}:{DB_PORT}")
    print(f" Target User:     {DB_USER}")
    print(f" Database Name:   {DB_NAME}")
    print("-" * 65)

    if not report["connected"]:
        print(" [FAIL] Server Connection: FAILED")
        for err in report["errors"]:
            print(f"        -> {err}")
        print("\n Troubleshooting Tips:")
        print("  1. Verify MySQL server is running:")
        print("     - Linux/Ubuntu: sudo systemctl status mysql")
        print("     - macOS:        brew services list  OR  mysql.server status")
        print("     - Windows:      Get-Service MySQL* (PowerShell)")
        print("  2. Check credentials in .env file (DB_HOST, DB_PORT, DB_USER, DB_PASSWORD).")
        print("=" * 65)
        return False

    print(" [OK] Server Connection: SUCCESS")

    if not report["database_exists"]:
        print(f" [FAIL] Database Status: Database '{DB_NAME}' does not exist.")
        print(f"        -> Run 'python database/init_db.py' to create and initialize it.")
        print("=" * 65)
        return False

    print(f" [OK] Database Status: '{DB_NAME}' exists")
    print("-" * 65)

    # Tables summary
    found_tables = set(report["tables"])
    missing_tables = [t for t in EXPECTED_TABLES if t not in found_tables]
    print(f" Tables:     {len(report['tables'])} found (Expected {len(EXPECTED_TABLES)})")
    if missing_tables:
        print(f"             Missing: {', '.join(missing_tables)}")
    else:
        print(f"             All {len(EXPECTED_TABLES)} core relational tables present.")

    # Record counts
    if report["record_counts"]:
        counts_str = ", ".join([f"{k}: {v}" for k, v in report["record_counts"].items()])
        print(f" Row Counts: {counts_str}")

    # Views summary
    found_views = set(report["views"])
    missing_views = [v for v in EXPECTED_VIEWS if v not in found_views]
    print(f" Views:      {len(report['views'])} found (Expected {len(EXPECTED_VIEWS)})")
    if missing_views:
        print(f"             Missing: {', '.join(missing_views)}")

    # Triggers summary
    found_triggers = set(report["triggers"])
    missing_triggers = [t for t in EXPECTED_TRIGGERS if t not in found_triggers]
    print(f" Triggers:   {len(report['triggers'])} found (Expected {len(EXPECTED_TRIGGERS)})")
    if missing_triggers:
        print(f"             Missing: {', '.join(missing_triggers)}")

    # Procedures summary
    found_procs = set(report["procedures"])
    missing_procs = [p for p in EXPECTED_PROCEDURES if p not in found_procs]
    print(f" Procedures: {len(report['procedures'])} found (Expected {len(EXPECTED_PROCEDURES)})")
    if missing_procs:
        print(f"             Missing: {', '.join(missing_procs)}")

    print("=" * 65)

    all_good = (
        not missing_tables and
        not missing_views and
        not missing_triggers and
        not missing_procs
    )
    if all_good:
        print(" Status: HEALTHY - Database is fully initialized and operational.")
    else:
        print(" Status: INCOMPLETE - Some schema objects are missing.")
        print(" Fix: Run 'python database/init_db.py --reset' to synchronize schema.")
    print("=" * 65)
    return all_good


def init_database(reset=False, seed=True, skip_seed=False, seed_only=False, force=False):
    """
    Perform reproducible initialization of the Meal Booking System database.
    Safe by default: refuses to drop existing data unless confirmed or --reset/--force passed.
    """
    db_dir = os.path.dirname(__file__)
    schema_file = os.path.join(db_dir, "schema.sql")
    seed_file = os.path.join(db_dir, "seed.sql")
    views_file = os.path.join(db_dir, "views.sql")
    triggers_file = os.path.join(db_dir, "triggers.sql")
    procedures_file = os.path.join(db_dir, "procedures.sql")

    # Check existing state first
    existing = check_database()
    if not existing["connected"]:
        print_check_report(existing)
        sys.exit(1)

    has_existing_tables = bool(existing["tables"])

    if seed_only:
        print(f" Seeding existing database '{DB_NAME}'...")
        conn = get_raw_connection(include_database=True)
        try:
            cnt = execute_sql_file(conn, seed_file)
            print(f" [OK] Executed {cnt} statements from seed.sql")
        finally:
            conn.close()
        print_check_report(check_database())
        return

    # Safety check if tables exist and not resetting
    if has_existing_tables and not reset:
        if not force:
            print("\n" + "!" * 65)
            print(" WARNING: ACCIDENTAL DATA RESET PREVENTION")
            print("!" * 65)
            print(f" The database '{DB_NAME}' already contains {len(existing['tables'])} tables:")
            print(f"   {', '.join(existing['tables'])}")
            print("\n Initializing will reset these tables and recreate all objects.")
            print(" To proceed with re-initializing, run with --reset or --force:")
            print("     python database/init_db.py --reset")
            print(" To inspect database health without modifying anything:")
            print("     python database/init_db.py --check")
            print("!" * 65)

            # Check if running interactively
            if sys.stdin.isatty():
                ans = input("\n Do you wish to proceed and reset the database? [y/N]: ").strip().lower()
                if ans not in ("y", "yes"):
                    print(" Initialization cancelled by user. No data was modified.")
                    return
            else:
                print(" Non-interactive environment detected. Aborting to protect existing data.")
                print(" Pass --reset or --force flag to confirm automated re-initialization.")
                sys.exit(1)

    print(f"\n Initializing Meal Booking System database '{DB_NAME}' at {DB_HOST}:{DB_PORT}...")

    # Step 1: Ensure database exists and run schema.sql
    conn_raw = get_raw_connection(include_database=False)
    try:
        with conn_raw.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    finally:
        conn_raw.close()

    conn = get_raw_connection(include_database=True)
    try:
        # Step 1: schema.sql
        print(" [1/5] Executing database/schema.sql...")
        s_cnt = execute_sql_file(conn, schema_file)
        print(f"       -> {s_cnt} statements executed successfully.")

        # Step 2: seed.sql (unless --skip-seed specified)
        if seed and not skip_seed:
            print(" [2/5] Executing database/seed.sql...")
            sd_cnt = execute_sql_file(conn, seed_file)
            print(f"       -> {sd_cnt} statements executed successfully.")
        else:
            print(" [2/5] Skipping database/seed.sql (--skip-seed requested).")

        # Step 3: views.sql
        print(" [3/5] Executing database/views.sql...")
        v_cnt = execute_sql_file(conn, views_file)
        print(f"       -> {v_cnt} statements executed successfully.")

        # Step 4: triggers.sql
        print(" [4/5] Executing database/triggers.sql...")
        t_cnt = execute_sql_file(conn, triggers_file)
        print(f"       -> {t_cnt} statements executed successfully.")

        # Step 5: procedures.sql
        print(" [5/5] Executing database/procedures.sql...")
        p_cnt = execute_sql_file(conn, procedures_file)
        print(f"       -> {p_cnt} statements executed successfully.")

    finally:
        conn.close()

    print("\n Verification Report:")
    report = check_database()
    success = print_check_report(report)
    if not success:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Meal Booking System - Database Initialization and Health Check Utility"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Perform non-destructive health and schema verification without modifying data."
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Force drop and recreate database schema, views, triggers, and procedures."
    )
    parser.add_argument(
        "--seed-only",
        action="store_true",
        help="Execute seed.sql on existing schema without recreating tables."
    )
    parser.add_argument(
        "--skip-seed",
        action="store_true",
        help="Initialize schema, views, triggers, and procedures without inserting seed records."
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Bypass interactive confirmation prompt when resetting existing database."
    )

    args = parser.parse_args()

    if args.check:
        report = check_database()
        success = print_check_report(report)
        sys.exit(0 if success else 1)

    init_database(
        reset=args.reset,
        skip_seed=args.skip_seed,
        seed_only=args.seed_only,
        force=args.force
    )


if __name__ == "__main__":
    main()
