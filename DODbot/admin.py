import openpyxl
from openpyxl.styles import Font, PatternFill
from database import db_manager


def create_admins_table():
    """Создание таблицы админов"""
    try:
        with db_manager.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    adminname TEXT PRIMARY KEY,
                    adminlevel INTEGER DEFAULT 1 CHECK(adminlevel IN (0, 1, 2)),
                    questnum INTEGER DEFAULT 0 CHECK(questnum BETWEEN 0 AND 11)
                )
            """)
            
    except Exception as e:
        print(f"Ошибка создания таблицы админов: {e}")


def add_admin(adminname: str, adminlevel: int) -> bool:
    """Добавление администратора"""
    try:
        with db_manager.get_connection() as conn:
            # Проверка существования администратора
            cursor = conn.execute(
                "SELECT 1 FROM admins WHERE adminname = ?",
                (adminname,)
            )
            if cursor.fetchone():
                print(f"⚠️ {adminname} уже является админом")
                return False

            conn.execute(
                "INSERT INTO admins (adminname, adminlevel) VALUES (?, ?)",
                (adminname, adminlevel)
            )
            
            return True
    except Exception as e:
        print(f"Ошибка добавления администратора: {e}")
        return False


def get_all_admins() -> list:
    """Получение списка всех админов"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM admins ORDER BY adminlevel DESC")
            return cursor.fetchall()
    except Exception as e:
        print(f"Ошибка получения списка админов: {e}")
        return []


def get_admin_level(username: str) -> int:
    """Получение уровня доступа админа"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT adminlevel FROM admins WHERE adminname = ?",
                (username,)
            )
            result = cursor.fetchone()
            return result[0] if result else 0
    except Exception as e:
        print(f"Ошибка получения уровня админа: {e}")
        return 0


def update_admin_questnum(username: str, new_value: int) -> bool:
    """Обновление номера станции для админа"""
    try:
        with db_manager.get_connection() as conn:
            conn.execute(
                "UPDATE admins SET questnum = ? WHERE adminname = ?",
                (new_value, username)
            )
            
            return True
    except Exception as e:
        print(f"Ошибка обновления станции админа: {e}")
        return False


def save_admins_to_excel():
    """Экспорт админов в Excel"""
    try:
        admins = get_all_admins()
        if not admins:
            return None

        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Админы"

        # Заголовки
        sheet.append(["Adminname", "Level", "Station"])

        # Данные
        for admin in admins:
            sheet.append(list(admin))

        # Стилизация заголовков
        header_fill = PatternFill(
            start_color="4F81BD",
            end_color="4F81BD",
            fill_type="solid"
        )
        header_font = Font(bold=True, color="FFFFFF")

        for cell in sheet[1]:
            cell.fill = header_fill
            cell.font = header_font

        filename = "admins.xlsx"
        workbook.save(filename)
        return filename
    except Exception as e:
        print(f"Ошибка экспорта в Excel: {e}")
        return None


def get_admin_by_username(username: str):
    """Поиск админа по username"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM admins WHERE adminname = ?",
                (username,)
            )
            return cursor.fetchone()
    except Exception as e:
        print(f"Ошибка поиска админа: {e}")
        return None


def init_admins():
    """Инициализация администраторов по умолчанию"""
    try:
        add_admin("@arrisse", 0)
        add_admin("@Nikita_Savel", 0)
    except Exception as e:
        print(f"Ошибка инициализации админов: {e}")
