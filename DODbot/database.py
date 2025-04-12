import aiosqlite
import asyncio
import logging
from filelock import FileLock
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class AsyncDatabaseManager:
    def __init__(self, db_path="base.db"):
        self.db_path = db_path

    @asynccontextmanager
    async def get_connection(self):
        # Получение файловой блокировки с переносом в синхронную задачу:

        conn = None
        try:
            conn = await aiosqlite.connect(self.db_path)
            # Настройка параметров работы SQLite
            await conn.execute("PRAGMA journal_mode=WAL")
            await conn.execute("PRAGMA busy_timeout=10000")
            # Передача соединения в контекст
            conn.row_factory = aiosqlite.Row
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

db_manager = AsyncDatabaseManager()
