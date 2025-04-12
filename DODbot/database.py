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
        try:
            # Блокировка файла вне асинхронной области
            await asyncio.to_thread(self.lock.acquire)

            conn = await aiosqlite.connect(self.db_path)
            await conn.execute("PRAGMA journal_mode=WAL")
            await conn.execute("PRAGMA busy_timeout=10000")

            try:
                yield conn
                await conn.commit()
            finally:
                await conn.close()

        except Exception as e:
            logger.critical(f"Ошибка подключения к БД: {e}")
            raise

        finally:
            if self.lock.is_locked:
                self.lock.release()


db_manager = AsyncDatabaseManager()
