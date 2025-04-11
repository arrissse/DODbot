import sqlite3
from threading import Lock
from contextlib import contextmanager
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

db_lock = Lock()
DATABASE = "base.db"


@contextmanager
def get_connection():
    """Потокобезопасный контекстный менеджер для подключений"""
    logger.debug("Ожидание блокировки БД...")
    with db_lock:
        logger.debug("Блокировка получена")
        conn = None
        try:
            conn = sqlite3.connect(
                DATABASE,
                check_same_thread=False,
                timeout=30
            )
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout = 5000")
            yield conn
            conn.commit()
        except Exception as e:
            logger.error(f"Ошибка подключения: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
            logger.debug("Блокировка освобождена")


@contextmanager
def db_operation():
    """Универсальный контекстный менеджер для всех операций с БД"""
    db_lock.acquire()
    try:
        conn = sqlite3.connect(DATABASE, check_same_thread=False, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        yield conn
        conn.commit()
    finally:
        conn.close()
        db_lock.release()
