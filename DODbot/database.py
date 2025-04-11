import sqlite3
from threading import Lock

db_lock = Lock()
DATABASE = "base.db"

def get_connection():
    conn = sqlite3.connect("base.db", check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    if not hasattr(conn, 'is_closed') or conn.is_closed:
        conn = sqlite3.connect(...)
    return conn


def close_connection(conn):
    if conn:
        conn.close()
