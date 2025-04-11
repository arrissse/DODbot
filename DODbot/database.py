import sqlite3
from threading import Lock

db_lock = Lock()
DATABASE = "base.db"


def get_connection():
    conn = sqlite3.connect(
        DATABASE,
        check_same_thread=False,
        timeout=30
    )
    conn.execute("PRAGMA journal_mode=WAL")
    return conn
