import sqlite3
from threading import Lock
from contextlib import contextmanager

db_lock = Lock()
DATABASE = "base.db"


@contextmanager
def get_connection():
    db_lock.acquire()
    conn = None
    try:
        conn = sqlite3.connect(
            DATABASE,
            check_same_thread=False,
            timeout=30
        )
        conn.execute("PRAGMA journal_mode=WAL")
        yield conn
        conn.commit()
    finally:
        if conn:
            conn.close()
        db_lock.release()
