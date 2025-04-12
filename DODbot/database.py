import sqlite3
import logging
from filelock import FileLock, Timeout
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self):
        self.lock = FileLock("database.lock", timeout=30)
        self.conn = None

    @contextmanager
    def get_connection(self):
        try:
            with self.lock.acquire(timeout=30):  # Увеличенный таймаут
                self.conn = sqlite3.connect(
                    "base.db",
                    check_same_thread=False,
                    timeout=5  # Увеличенный таймаут подключения
                )
                self.conn.execute("PRAGMA journal_mode=WAL")
                self.conn.execute("PRAGMA busy_timeout=10000")
                yield self.conn
                if self.conn is None:
                    logger.error("Соединение не установлено!")
                    return
                self.conn.commit()
        except Exception as e:
            logger.critical(f"Ошибка подключения: {str(e)}")
            raise
        finally:
            if self.conn:
                self.conn.close()
                self.conn = None


db_manager = DatabaseManager()
