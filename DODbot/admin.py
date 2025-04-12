import sqlite3
import openpyxl
from openpyxl.styles import Font, PatternFill
from database import db_manager


def init_admins():
    try:
        add_admin("@arrisse", 0)
        add_admin("@Nikita_Savel", 0)
    except Exception as e:
        print(f"Ошибка инициализации админов: {e}")


def create_admins_table():
  with db_manager.get_connection() as conn:
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        adminname TEXT,            -- Имя пользователя (@username)
        adminlevel INTEGER DEFAULT 1, -- Уровень админства
        questnum INTEGER DEFAULT 0 -- Номер станции (если админ второго уровня)
    )
    """)


def add_admin(adminname, adminlevel):

  with db_manager.get_connection() as conn:
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM admins WHERE adminname = ?", (adminname,))
    exists = cursor.fetchone()[0]

    if exists:
        print(f"⚠️ {adminname} уже является админом.")
        conn.close()
        return False
    cursor.execute("INSERT OR IGNORE INTO admins (adminname, adminlevel) VALUES (?, ?)",
                   (adminname, adminlevel))
    return True


def get_all_admins():
  with db_manager.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admins")
    admins = cursor.fetchall()
    return [(admin) for admin in admins]


def get_admin_level(username):
  with db_manager.get_connection() as conn:
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT adminlevel FROM admins WHERE adminname = ?", (username,))
        result = cursor.fetchone()
    except Exception as e:
        print("Ошибка при выполнении запроса:", e)
        result = None
    return result[0] if result is not None else 0


def update_admin_questnum(username, new_value):
  with db_manager.get_connection() as conn:
    cursor = conn.cursor()

    cursor.execute(
        f"UPDATE admins SET questnum = ? WHERE adminname = ?", (new_value, username))


def save_admins_to_excel():
    users = get_all_admins()

    if not users:
        return None

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Админы"

    sheet.append(["Adminname", "level", "station"])

    for user in users:
        sheet.append(list(user))

    filename = "admins.xlsx"
    workbook.save(filename)
    return filename


def get_admin_by_username(username):
  with db_manager.get_connection() as conn:
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM admins WHERE adminname = ?", (username,))
    user = cursor.fetchone()
    return user if user else None
