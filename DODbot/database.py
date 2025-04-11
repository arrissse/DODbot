import sqlite3
import threading
import time
import logging
from contextlib import contextmanager
from filelock import FileLock, Timeout

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class DatabaseManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.connection_lock = threading.Lock()
                cls._instance.init_db()
            return cls._instance

    def __init__(self):
        self.lock = FileLock("database.lock", timeout=30)
        self.conn = None

    def init_db(self):
        self.conn = sqlite3.connect(
            "base.db",
            check_same_thread=False,
            timeout=60
        )
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=5000")

    def get_connection(self):
        try:
            with self.lock:
                self.conn = sqlite3.connect('database.db', timeout=20)
                # Включить режим WAL
                self.conn.execute("PRAGMA journal_mode=WAL")
                yield self.conn
        except Timeout:
            logger.error("Превышено время ожидания блокировки")
            raise
        finally:
            if self.conn:
                self.conn.close()

    def is_initialized(self):
      try:
        with self.get_connection(timeout=1) as conn:
            conn.execute("SELECT 1 FROM sqlite_master WHERE type='table'")
            return True
      except Exception:
        return False


# Глобальный экземпляр менеджера
db_manager = DatabaseManager()
