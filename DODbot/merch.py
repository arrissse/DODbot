import openpyxl
from database import db_manager
import asyncpg


async def create_merch_table():
    async with db_manager.pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS merch (
                username TEXT UNIQUE,
                "Раскрасить футболку" INTEGER DEFAULT 0,
                "Раскрасить шоппер" INTEGER DEFAULT 0,
                "Футболка" INTEGER DEFAULT 0,
                "Блокнот" INTEGER DEFAULT 0,
                "ПБ" INTEGER DEFAULT 0
            )
        """)


async def is_valid_column(column_name: str) -> bool:
    async with db_manager.pool.acquire() as conn:
        columns = await conn.fetch(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'merch'"
        )
        return any(column['column_name'] == column_name for column in columns)


async def got_merch(username: str, type: str) -> bool:
    if not await is_valid_column(type):
        raise ValueError(f"Недопустимое имя колонки: {type}")

    async with db_manager.pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO merch (username) VALUES ($1) ON CONFLICT (username) DO NOTHING",
            username
        )
        result = await conn.fetchval(
            f'SELECT "{type}" FROM merch WHERE username = $1',
            username
        )
        return result == 1


async def give_merch(username: str, type: str):
    if not await is_valid_column(type):
        raise ValueError(f"Недопустимое имя колонки: {type}")

    async with db_manager.pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO merch (username) VALUES ($1) ON CONFLICT (username) DO NOTHING",
            username
        )
        await conn.execute(
            f'UPDATE merch SET "{type}" = 1 WHERE username = $1',
            username
        )


async def is_got_merch(username: str) -> bool:
    async with db_manager.pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO merch (username) VALUES ($1) ON CONFLICT (username) DO NOTHING",
            username
        )

        columns = await conn.fetch(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'merch' AND data_type IN ('integer', 'real')"
        )
        numeric_columns = [col['column_name']
                           for col in columns if col['column_name'] != 'username']

        if not numeric_columns:
            return False

        sum_query = " + ".join([f'"{col}"' for col in numeric_columns])
        result = await conn.fetchval(
            f"SELECT ({sum_query}) = {len(numeric_columns)} FROM merch WHERE username = $1",
            username
        )
        return bool(result)


async def is_got_any_merch(username: str) -> bool:
    async with db_manager.pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO merch (username) VALUES ($1) ON CONFLICT (username) DO NOTHING",
            username
        )

        columns = await conn.fetch(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'merch' AND data_type IN ('integer', 'real')"
        )
        numeric_columns = [col['column_name']
                           for col in columns if col['column_name'] != 'username']

        if not numeric_columns:
            return False

        sum_query = " + ".join([f'"{col}"' for col in numeric_columns])
        result = await conn.fetchval(
            f"SELECT ({sum_query}) > 0 FROM merch WHERE username = $1",
            username
        )
        return bool(result)


async def add_column(column_name: str, column_type: str = "INTEGER DEFAULT 0"):
    async with db_manager.pool.acquire() as conn:
        exists = await conn.fetchval(
            "SELECT EXISTS ("
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = 'merch' AND column_name = $1"
            ")",
            column_name
        )

        if not exists:
            await conn.execute(
                f"ALTER TABLE merch ADD COLUMN {column_name} {column_type}"
            )
            print(f"Столбец '{column_name}' добавлен в таблицу.")
        else:
            print(f"Столбец '{column_name}' уже существует.")


async def get_all_merch():
    async with db_manager.pool.acquire() as conn:
        return await conn.fetch("SELECT * FROM merch")


async def get_table_columns(table_name: str):
    async with db_manager.pool.acquire() as conn:
        columns = await conn.fetch(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = $1",
            table_name
        )
        return [col['column_name'] for col in columns]


async def save_merch_to_excel():
    merch = await get_all_merch()
    columns = await get_table_columns('merch')

    if not merch:
        return None

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Мерч"

    sheet.append(columns)

    for item in merch:
        sheet.append(list(item.values()))

    filename = "merch.xlsx"
    workbook.save(filename)
    return filename
