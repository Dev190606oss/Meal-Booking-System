import pymysql
import pymysql.cursors
from contextlib import contextmanager
from app.config import Config

def get_db_connection(database=Config.DB_NAME):
    """Establish and return a new MySQL connection using PyMySQL."""
    kwargs = {
        "host": Config.DB_HOST,
        "port": Config.DB_PORT,
        "user": Config.DB_USER,
        "password": Config.DB_PASSWORD,
        "database": database,
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": True
    }
    if Config.DB_SSL:
        kwargs["ssl"] = {"ssl_mode": "REQUIRED", "check_hostname": False}

    return pymysql.connect(**kwargs)

def test_db_connection():
    """
    Test database connection and verify presence of required schema objects.
    Returns a dictionary containing health status and troubleshooting suggestions.
    """
    status = {
        "connected": False,
        "database_exists": False,
        "table_count": 0,
        "tables": [],
        "error": None,
        "troubleshooting": []
    }

    # Step 1: Connect to MySQL server
    try:
        conn = get_db_connection(database=None)
    except Exception as e:
        status["error"] = str(e)
        status["troubleshooting"] = [
            f"Verify MySQL service is running on {Config.DB_HOST}:{Config.DB_PORT}.",
            "On Linux/Ubuntu: sudo systemctl status mysql (or sudo systemctl start mysql)",
            "On macOS: brew services list (or brew services start mysql)",
            "On Windows (PowerShell): Get-Service MySQL* (or net start MySQL80)",
            f"Check DB_HOST, DB_PORT ({Config.DB_PORT}), DB_USER ('{Config.DB_USER}'), and DB_PASSWORD in your .env file."
        ]
        return status

    status["connected"] = True

    try:
        with conn.cursor() as cur:
            # Step 2: Check if target database exists
            cur.execute("SHOW DATABASES LIKE %s", (Config.DB_NAME,))
            if not cur.fetchone():
                status["error"] = f"Database '{Config.DB_NAME}' does not exist."
                status["troubleshooting"] = [
                    f"Create and initialize the database schema by running:",
                    "    python database/init_db.py",
                    f"Or manually: CREATE DATABASE `{Config.DB_NAME}`; in MySQL client."
                ]
                return status

            status["database_exists"] = True
            cur.execute(f"USE `{Config.DB_NAME}`")

            # Step 3: Count base tables
            cur.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = %s AND table_type = 'BASE TABLE'",
                (Config.DB_NAME,)
            )
            tables = sorted([row.get("TABLE_NAME") or row.get("table_name") for row in cur.fetchall()])
            status["tables"] = tables
            status["table_count"] = len(tables)

            if len(tables) == 0:
                status["troubleshooting"] = [
                    f"Database '{Config.DB_NAME}' exists but contains 0 tables.",
                    "Run 'python database/init_db.py' to populate tables, views, triggers, and seed data."
                ]
    except Exception as e:
        status["error"] = str(e)
    finally:
        conn.close()

    return status

def query_db(sql, args=(), one=False):
    """Execute a SELECT query and return fetched dictionaries."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, args)
            results = cursor.fetchall()
            return (results[0] if results else None) if one else results
    finally:
        conn.close()

def execute_db(sql, args=()):
    """Execute an INSERT, UPDATE, or DELETE statement and return lastrowid and affected rows."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            affected = cursor.execute(sql, args)
            last_id = cursor.lastrowid
            return {"last_id": last_id, "affected": affected}
    finally:
        conn.close()

def call_proc(proc_name, args=()):
    """Call a stored procedure and return result sets."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.callproc(proc_name, args)
            results = cursor.fetchall()
            return results
    finally:
        conn.close()

@contextmanager
def get_transaction_cursor():
    """Context manager for multi-query atomic transactions."""
    conn = get_db_connection()
    conn.autocommit(False)
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
