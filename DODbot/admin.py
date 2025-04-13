from bot import bot, dp, router
from aiogram.types import BufferedInputFile
from database import db_manager
import openpyxl
from openpyxl.styles import Font, PatternFill
import asyncio
from io import BytesIO
from openpyxl import Workbook
from aiogram.types import BufferedInputFile

async def init_admins():
    try:
        await add_admin("@arrisse", 0)
        await add_admin("@Nikita_Savel", 0)
    
        await add_admin("@thelasttime111th", 2)
        await update_admin_questnum("@thelasttime111th", 9)

        await add_admin("@sobolevski", 2)
        await update_admin_questnum("@sobolevski", 10)

        await add_admin("@FilippovaEA", 2)
        await update_admin_questnum("@FilippovaEA", 8)

        await add_admin("@rainsmaker", 2)
        await update_admin_questnum("@rainsmaker", 7)

        await add_admin("@divenire3", 2)
        await update_admin_questnum("@divenire3", 1)

        await add_admin("@nalyotova", 2)
        await update_admin_questnum("@nalyotova", 6)
        await add_admin("@amy_ayr", 2)
        await update_admin_questnum("@amy_ayr", 4)

        await add_admin("@IRISHA_tay", 2)
        await update_admin_questnum("@IRISHA_tay", 5)

        await add_admin("@dmitrieva_p", 2)
        await update_admin_questnum("@dmitrieva_p", 3)

        await add_admin("@bonderson", 2)
        await update_admin_questnum("@bonderson", 11)

        await add_admin("@catmorozz", 2)
        await update_admin_questnum("@catmorozz", 11)

        await add_admin("@lovetea10", 2)
        await update_admin_questnum("@lovetea10", 11)
    
        await add_admin("@kson27", 1)
        await add_admin("@carefree_celery", 1)
        await add_admin("@Lost_Soull8", 1)
        await add_admin("@soniaaak", 1)
        await add_admin("@iourok", 1)

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
        try:
            # Проверка существования администратора
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
        except Exception as e:
            await conn.rollback()
            raise


async def get_all_admins():
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


async def save_admins_to_excel(bot):
    admins = await get_all_admins()

    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Username", "Level", "Station"])

    for admin in admins:
        sheet.append([admin[0], admin[1], admin[2]])

    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    return BufferedInputFile(
        file=buffer.read(),
        filename="admins.xlsx"
    )


async def get_admin_by_username(username: str):
    async with db_manager.get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            "SELECT * FROM admins WHERE adminname = ?",
            (username,)
        )
        return await cursor.fetchone()
