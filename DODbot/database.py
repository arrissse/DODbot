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
        self.lock = FileLock("database.lock", timeout=60)

    def init_db(self):
        self.conn = sqlite3.connect(
            "base.db",
            check_same_thread=False,
            timeout=60
        )
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=5000")

    @contextmanager
    def get_connection(self):
        """Потокобезопасное подключение с таймаутом"""
        start_time = time.time()
        timeout = 30  # Максимальное время ожидания

        while True:
            if self.connection_lock.acquire(blocking=False):
                try:
                    logger.debug("🔒 Блокировка БД получена")
                    yield self.conn
                    self.conn.commit()
                    break
                finally:
                    self.connection_lock.release()
                    logger.debug("🔓 Блокировка БД освобождена")
            else:
                if time.time() - start_time > timeout:
                    raise TimeoutError("Не удалось получить блокировку БД")
                logger.debug("⌛ Ожидание блокировки...")
                time.sleep(1)

    def is_initialized(self):
      try:
        with self.get_connection(timeout=1) as conn:
            conn.execute("SELECT 1 FROM sqlite_master WHERE type='table'")
            return True
      except Exception:
        return False


# Глобальный экземпляр менеджера
db_manager = DatabaseManager()
