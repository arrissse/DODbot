from bot import bot, dp, router
from aiogram.types import BufferedInputFile
from database import db_manager
import openpyxl
from openpyxl.styles import Font, PatternFill
import asyncio


async def init_admins():
    try:
        await add_admin("@arrisse", 0)
        await add_admin("@Nikita_Savel", 0)
    except Exception as e:
        print(f"Ошибка инициализации админов: {e}")


async def create_admins_table():
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


async def add_admin(adminname: str, adminlevel: int) -> bool:
    async with db_manager.get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            "SELECT COUNT(*) FROM admins WHERE adminname = ?",
            (adminname,)
        )
        exists = (await cursor.fetchone())[0]

        if exists:
            print(f"⚠️ {adminname} уже является админом.")
            return False

        await cursor.execute(
            "INSERT OR IGNORE INTO admins (adminname, adminlevel) VALUES (?, ?)",
            (adminname, adminlevel)
        )
        await conn.commit()
        return True


async def update_admin_info(adminname: str, admin_level: int):
    async with db_manager.get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            "UPDATE admins SET adminlevel = ? WHERE adminname = ?",
            (admin_level, adminname)
        )
        await conn.commit()


async def get_all_admins() -> list:
    async with db_manager.get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute("SELECT * FROM admins")
        return [admin for admin in await cursor.fetchall()]


async def get_admin_level(username: str) -> int:
    async with db_manager.get_connection() as conn:
        cursor = await conn.cursor()
        try:
            await cursor.execute(
                "SELECT adminlevel FROM admins WHERE adminname = ?",
                (username,)
            )
            result = await cursor.fetchone()
        except Exception as e:
            print("Ошибка при выполнении запроса:", e)
            return 0
        return result[0] if result else 0


async def update_admin_questnum(username: str, new_value: int):
    async with db_manager.get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            "UPDATE admins SET questnum = ? WHERE adminname = ?",
            (new_value, username)
        )
        await conn.commit()


async def save_admins_to_excel(bot) -> BufferedInputFile:
    admins = await get_all_admins()

    if not admins:
        return None

    # Синхронные операции выполняем в отдельном потоке
    def generate_excel():
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Админы"
        sheet.append(["Adminname", "Level", "Station"])

        for admin in admins:
            sheet.append(list(admin))

        filename = "admins.xlsx"
        workbook.save(filename)
        return filename

    loop = asyncio.get_event_loop()
    filename = await loop.run_in_executor(None, generate_excel)

    with open(filename, 'rb') as file:
        return BufferedInputFile(file.read(), filename="admins_list.xlsx")


async def get_admin_by_username(username: str):
    async with db_manager.get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            "SELECT * FROM admins WHERE adminname = ?",
            (username,)
        )
        return await cursor.fetchone()
