import openpyxl
from database import db_manager
import asyncpg


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


async def is_valid_column(column_name: str) -> bool:
    async with db_manager.get_connection() as conn:
        columns = await conn.fetch(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'merch'"
        )
        return any(column['column_name'] == column_name for column in columns)


async def got_merch(username: str, type: str) -> bool:
    if not await is_valid_column(type):
        raise ValueError(f"Недопустимое имя колонки: {type}")

    async with db_manager.get_connection() as conn:
        await conn.execute(
                "INSERT OR IGNORE INTO merch (username) VALUES (?)",
                (username,)
            )
        await conn.commit()  # Явное подтверждение изменений
            
            # Проверяем наличие мерча
        async with conn.execute(
                f'SELECT "{type}" FROM merch WHERE username = ?',
                (username,)
            ) as cursor:
                result = await cursor.fetchone()
                return result and result[0] == 1

async def give_merch(username: str, type: str):
    if not await is_valid_column(type):
        raise ValueError(f"Недопустимое имя колонки: {type}")

    async with db_manager.get_connection() as conn:
        await conn.execute(
            "INSERT INTO merch (username) VALUES (?) ON CONFLICT (username) DO NOTHING",
            username
        )
        await conn.execute(
            f'UPDATE merch SET "{type}" = 1 WHERE username = ?',
            (username, )
        )


async def is_got_merch(username: str) -> bool:
    async with db_manager.get_connection() as conn:
        await conn.execute(
            "INSERT INTO merch (username) VALUES (?) ON CONFLICT (username) DO NOTHING",
            (username, )
        )
        await conn.commit()

            # Получаем список числовых колонок (кроме username)
        async with conn.execute(
                "SELECT name FROM pragma_table_info('merch') WHERE type IN ('INTEGER', 'REAL')"
            ) as cursor:
                numeric_columns = [row[0] for row in await cursor.fetchall() 
                                 if row[0] != 'username']

        if not numeric_columns:
                return False

            # Создаем условие проверки для всех колонок
        check_conditions = " AND ".join([f'"{col}" = 1' for col in numeric_columns])
        query = f"""
                SELECT CASE WHEN ({check_conditions}) THEN 1 ELSE 0 END
                FROM merch 
                WHERE username = ?
            """
            
        async with conn.execute(query, (username,)) as cursor:
                result = await cursor.fetchone()
                return bool(result[0]) if result else False


async def is_got_any_merch(username: str) -> bool:
    async with db_manager.get_connection() as conn:
        await conn.execute(
            "INSERT INTO merch (username) VALUES (?) ON CONFLICT (username) DO NOTHING",
            (username, )
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
        result = await conn.fetchone(
            f"SELECT ({sum_query}) > 0 FROM merch WHERE username = ?",
            (username, )
        )
        return bool(result[0]) if result else False


async def add_column(column_name: str, column_type: str = "INTEGER DEFAULT 0"):
    async with db_manager.get_connection() as conn:
        result = await conn.fetchone(
            "SELECT EXISTS ("
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = 'merch' AND column_name = ?"
            ") AS column_exists",
            column_name
        )

        exists = result[0] if result else False

        if not exists:
            await conn.execute(
                f"ALTER TABLE merch ADD COLUMN {column_name} {column_type}"
            )
            print(f"Столбец '{column_name}' добавлен в таблицу.")
        else:
            print(f"Столбец '{column_name}' уже существует.")


async def get_all_merch():
    async with db_manager.get_connection() as conn:
        return await conn.fetch("SELECT * FROM merch")


async def get_table_columns(table_name: str):
    async with db_manager.get_connection() as conn:
        columns = await conn.fetch(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = ?",
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
