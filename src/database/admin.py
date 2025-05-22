from openpyxl import Workbook

from constants import ADMIN_FILENAME, ADMIN_TITLE
from src.database.base import db_manager


async def init_admins():
    """
    Initialize the default set of administrators in the database.

    Inserts or updates a predefined list of admin users with their
    respective permission levels and, for level-2 admins, assigns them
    to specific quest stations.
    """
    try:
        await add_admin("@arrisse", 0)
        await add_admin("@Nikita_Savel", 0)

        await add_admin("@thelasttime111th", 2)
        await update_admin_questnum("@thelasttime111th", 9)

        await add_admin("@kson27", 1)

    except Exception as err:
        print(f"Ошибка инициализации админов: {err}")


async def create_admins_table():
    """
    Create the `admins` table if it does not already exist.

    The table schema is:
        - adminname TEXT PRIMARY KEY
        - adminlevel INTEGER DEFAULT 1
        - questnum INTEGER DEFAULT 0

    This function must be called before any admin operations.
    """
    async with db_manager.get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                adminname TEXT,
                adminlevel INTEGER DEFAULT 1,
                questnum INTEGER DEFAULT 0
            )
        """)
        await conn.commit()


async def add_admin(adminname, adminlevel):
    """
    Add a new administrator or update an existing one.

    If an entry with `adminname` already exists, updates its level.
    Otherwise, inserts a new row.

    Args:
        adminname (str): The Telegram username of the admin (including '@').
        adminlevel (int): Permission level (0 = super-admin, 1 = merch, 2 = station).

    Returns:
        bool: True on success.

    Raises:
        Exception: On any database error; the transaction will be rolled back.
    """
    async with db_manager.get_connection() as conn:
        try:
            cursor = await conn.execute(
                "SELECT * FROM admins WHERE adminname = ?",
                (adminname,)
            )
            is_exists = await cursor.fetchone()
            if is_exists:
                await cursor.execute(
                    "UPDATE admins SET adminlevel = ? WHERE adminname = ?",
                    (adminlevel, adminname)
                )
            else:
                await conn.execute(
                    "INSERT INTO admins (adminname, adminlevel) VALUES (?, ?)",
                    (adminname, adminlevel)
                )
                await conn.commit()
            return True
        except Exception:
            await conn.rollback()
            raise


async def get_all_admins():
    """
    Retrieve all administrator records.

    Returns:
        List[tuple]: Each tuple is (adminname, adminlevel, questnum).
    """
    async with db_manager.get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute("SELECT * FROM admins")
        rows = await cursor.fetchall()
        return [tuple(row) for row in rows]


async def get_admin_level(username):
    """
    Get the permission level for a given admin.

    Args:
        username (str): The Telegram username of the admin (including '@').

    Returns:
        int: The adminlevel (default 0 if not found or on error).
    """
    async with db_manager.get_connection() as conn:
        cursor = await conn.cursor()
        try:
            await cursor.execute(
                "SELECT adminlevel FROM admins WHERE adminname = ?",
                (username,)
            )
            result = await cursor.fetchone()
        except Exception as err:
            print("Ошибка при выполнении запроса:", err)
            return 0
        return result[0] if result else 0


async def update_admin_questnum(username, new_value):
    """
    Assign or change the station number for a level-2 admin.

    Args:
        username (str): The Telegram username of the admin (including '@').
        new_value (int): The quest station number to assign.
    """
    async with db_manager.get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            "UPDATE admins SET questnum = ? WHERE adminname = ?",
            (new_value, username)
        )
        await conn.commit()


async def save_admins_to_excel():
    """
    Export the admins table to an in-memory Excel file.

    - Columns: Username, Level, Station
    - Returns a BufferedInputFile suitable for sending via Telegram.

    Returns:
        BufferedInputFile: An object wrapping the bytes of "admins.xlsx".
    """
    admins = await get_all_admins()

    workbook = Workbook()
    sheet = workbook.active
    sheet.append(ADMIN_TITLE)

    for admin in admins:
        sheet.append([admin[0], admin[1], admin[2]])
    workbook.save(ADMIN_FILENAME)
    return ADMIN_FILENAME


async def get_admin_by_username(username):
    """
    Fetch a single admin record by username.

    Args:
        username (str): The Telegram username of the admin (including '@').

    Returns:
        tuple: (adminname, adminlevel, questnum) if found.
        None: If no such admin exists.
    """
    async with db_manager.get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            "SELECT * FROM admins WHERE adminname = ?",
            (username,)
        )
        return await cursor.fetchone()
