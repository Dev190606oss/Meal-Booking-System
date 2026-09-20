import pymysql
import pymysql.cursors
from contextlib import contextmanager
from app.config import Config

def get_db_connection():
    """Establish and return a new MySQL connection using PyMySQL."""
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

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
