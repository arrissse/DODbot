import sqlite3
from threading import Lock

db_lock = Lock()


def get_connection():
    conn = sqlite3.connect("base.db", check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn
