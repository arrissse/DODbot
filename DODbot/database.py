import aiosqlite
import asyncio
import logging
from filelock import FileLock
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class AsyncDatabaseManager:
    def __init__(self, db_path="base.db", lock_path="database.lock"):
        self.db_path = db_path
        self.lock = FileLock(lock_path, timeout=30)

    @asynccontextmanager
    async def get_connection(self):
        # Получение файловой блокировки с переносом в синхронную задачу:
        try:
            await asyncio.to_thread(self.lock.acquire)
        except Exception as e:
            logger.critical(f"Не удалось получить файловую блокировку: {e}")
            raise

        conn = None
        try:
            conn = await aiosqlite.connect(self.db_path)
            # Настройка параметров работы SQLite
            await conn.execute("PRAGMA journal_mode=WAL")
            await conn.execute("PRAGMA busy_timeout=10000")
            # Передача соединения в контекст
            yield conn
            await conn.commit()
        except Exception as e:
            logger.critical(f"Ошибка подключения или работы с БД: {e}")
            raise
        finally:
            # Закрытие соединения, если оно было создано
            if conn:
                await conn.close()
            # Освобождаем блокировку, если она захвачена
            if self.lock.is_locked:
                try:
                    self.lock.release()
                except Exception as e:
                    logger.error(f"Ошибка освобождения блокировки: {e}")


db_manager = AsyncDatabaseManager()
