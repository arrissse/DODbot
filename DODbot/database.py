import sqlite3
from threading import Lock
from contextlib import contextmanager

db_lock = Lock()
DATABASE = "merch.db"


@contextmanager
def get_connection():
    with db_lock:
        conn = None
        try:
            conn = sqlite3.connect(
                DATABASE,
                check_same_thread=False,
                timeout=30
            )
            conn.execute("PRAGMA journal_mode=WAL")
            yield conn
        finally:
            if conn:
                conn.close()
