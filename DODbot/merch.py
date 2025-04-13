import openpyxl
from database import db_manager
import asyncpg  # если он используется где-то ещё, но для aiosqlite не нужен


async def create_merch_table():
    async with db_manager.get_connection() as conn:
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
        await conn.commit()


async def is_valid_column(column_name: str) -> bool:
    async with db_manager.get_connection() as conn:
        cursor = await conn.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'merch'"
        )
        columns = await cursor.fetchall()
        return any(row[0] == column_name for row in columns)


async def got_merch(username: str, merch_type: str) -> bool:
    if not await is_valid_column(merch_type):
        raise ValueError(f"Недопустимое имя колонки: {merch_type}")

    async with db_manager.get_connection() as conn:
        # Вставляем, если отсутствует запись для пользователя
        await conn.execute(
            "INSERT OR IGNORE INTO merch (username) VALUES (?)",
            (username,)
        )
        await conn.commit()
        cursor = await conn.execute(
            f'SELECT "{merch_type}" FROM merch WHERE username = ?',
            (username,)
        )
        result = await cursor.fetchone()
        return result is not None and result[0] == 1


async def give_merch(username: str, merch_type: str):
    if not await is_valid_column(merch_type):
        raise ValueError(f"Недопустимое имя колонки: {merch_type}")

    async with db_manager.get_connection() as conn:
        await conn.execute(
            "INSERT INTO merch (username) VALUES (?) ON CONFLICT (username) DO NOTHING",
            (username, )
        )
        await conn.execute(
            f'UPDATE merch SET "{merch_type}" = 1 WHERE username = ?',
            (username,)
        )
        await conn.commit()


async def is_got_merch(username: str) -> bool:
    async with db_manager.get_connection() as conn:
        await conn.execute(
            "INSERT INTO merch (username) VALUES (?) ON CONFLICT (username) DO NOTHING",
            (username,)
        )
        await conn.commit()

        cursor = await conn.execute(
            "SELECT name FROM pragma_table_info('merch') WHERE type IN ('INTEGER', 'REAL')"
        )
        rows = await cursor.fetchall()
        numeric_columns = [row[0] for row in rows if row[0] != 'username']

        if not numeric_columns:
            return False

        check_conditions = " AND ".join(
            [f'"{col}" = 1' for col in numeric_columns])
        query = f"""
                SELECT CASE WHEN ({check_conditions}) THEN 1 ELSE 0 END
                FROM merch 
                WHERE username = ?
            """
        cursor2 = await conn.execute(query, (username,))
        result = await cursor2.fetchone()
        return bool(result[0]) if result else False


async def is_got_any_merch(username: str) -> bool:
    async with db_manager.get_connection() as conn:
        await conn.execute(
            "INSERT INTO merch (username) VALUES (?) ON CONFLICT (username) DO NOTHING",
            (username, )
        )
        cursor = await conn.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'merch' AND data_type IN ('integer', 'real')"
        )
        columns = await cursor.fetchall()
        numeric_columns = [col[0] for col in columns if col[0] != 'username']

        if not numeric_columns:
            return False

        sum_query = " + ".join([f'"{col}"' for col in numeric_columns])
        cursor2 = await conn.execute(
            f"SELECT ({sum_query}) > 0 FROM merch WHERE username = ?",
            (username,)
        )
        result = await cursor2.fetchone()
        return bool(result[0]) if result else False


async def add_column(column_name: str, column_type: str = "INTEGER DEFAULT 0"):
    async with db_manager.get_connection() as conn:
        cursor = await conn.execute(
            "SELECT EXISTS ("
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = 'merch' AND column_name = ?"
            ") AS column_exists",
            (column_name, )
        )
        result = await cursor.fetchone()
        exists = result[0] if result else False

        if not exists:
            await conn.execute(
                f"ALTER TABLE merch ADD COLUMN {column_name} {column_type}"
            )
            print(f"Столбец '{column_name}' добавлен в таблицу.")
        else:
            print(f"Столбец '{column_name}' уже существует.")
        await conn.commit()


async def get_all_merch():
    async with db_manager.get_connection() as conn:
        cursor = await conn.execute("SELECT * FROM merch")
        return await cursor.fetchall()


async def get_table_columns(table_name: str):
    async with db_manager.get_connection() as conn:
        cursor = await conn.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = ?",
            (table_name, )
        )
        columns = await cursor.fetchall()
        return [col[0] for col in columns]


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
        # Если item – это кортеж, преобразуем его в список
        sheet.append(list(item))

    filename = "merch.xlsx"
    workbook.save(filename)
    return filename
