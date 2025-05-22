import logging
from contextlib import asynccontextmanager

import aiosqlite

logger = logging.getLogger(__name__)


class AsyncDatabaseManager:
    """
    Asynchronous context manager for SQLite database connections.

    Provides a simple interface for acquiring and releasing connections
    to an SQLite database using a WAL journal mode and a busy timeout.

    Usage:
        db_manager = AsyncDatabaseManager("my_database.db")
        async with db_manager.get_connection() as conn:
            # perform async DB operations on conn
            await conn.execute("...")
            ...

    Attributes:
        db_path (str): Filesystem path to the SQLite database file.
    """

    def __init__(self, db_path="base.db"):
        """
        Initialize the AsyncDatabaseManager.

        Args:
            db_path (str): Path to the SQLite database file.
                           Defaults to "base.db" in the current directory.
        """
        self.db_path = db_path

    @asynccontextmanager
    async def get_connection(self):
        """
        Acquire an asynchronous SQLite connection with recommended pragmas.

        This method is an async context manager that yields an
        `aiosqlite.Connection` object with the following settings:
          - WAL journal mode for better concurrency.
          - A busy timeout of 10,000 ms to wait for locks.
          - `row_factory` set to `aiosqlite.Row` for dict-like row access.

        On exit, commits any pending transaction and closes the connection.
        If an error occurs during acquisition or operations, logs a critical
        error and re-raises the exception.

        Yields:
            aiosqlite.Connection: An open SQLite connection.

        Raises:
            Exception: Propagates any exception that occurs while connecting,
                       setting pragmas, committing, or closing.
        """

        conn = None
        try:
            conn = await aiosqlite.connect(self.db_path)
            await conn.execute("PRAGMA journal_mode=WAL")
            await conn.execute("PRAGMA busy_timeout=10000")
            conn.row_factory = aiosqlite.Row
            yield conn
            await conn.commit()
        except Exception as err:
            logger.critical("Ошибка подключения или работы с БД: %s", err)
            raise
        finally:
            if conn:
                await conn.close()


db_manager = AsyncDatabaseManager()
