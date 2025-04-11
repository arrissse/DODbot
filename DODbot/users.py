import openpyxl
from openpyxl.styles import Font, PatternFill
from merch import is_got_any_merch
from database import db_manager  # Изменён импорт


def create_users_table():
    """Создание таблицы пользователей"""
    try:
        with db_manager.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT,
                    quest_started INTEGER DEFAULT 0,
                    quest1_points INTEGER DEFAULT 0,
                    quest2_points INTEGER DEFAULT 0,
                    quest3_points INTEGER DEFAULT 0,
                    quest4_points INTEGER DEFAULT 0,
                    quest5_points INTEGER DEFAULT 0,
                    quest6_points INTEGER DEFAULT 0,
                    quest7_points INTEGER DEFAULT 0,
                    quest8_points INTEGER DEFAULT 0,
                    quest9_points INTEGER DEFAULT 0,
                    quest10_points INTEGER DEFAULT 0,
                    quest11_points INTEGER DEFAULT 0,
                    quest_station INTEGER DEFAULT 0,
                    quest_points INTEGER DEFAULT 0,
                    quize_points INTEGER DEFAULT 0,
                    quize_1 INTEGER DEFAULT 0,
                    quize_2 INTEGER DEFAULT 0,
                    quize_3 INTEGER DEFAULT 0,
                    quize_4 INTEGER DEFAULT 0,
                    quize_5 INTEGER DEFAULT 0
                )
            """)
            conn.commit()
    except Exception as e:
        print(f"Error creating users table: {e}")


def add_user(user_id, username):
    """Добавление пользователя"""
    try:
        with db_manager.get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)",
                (user_id, username)
            )
            conn.commit()
    except Exception as e:
        print(f"Error adding user: {e}")


def get_user_by_username(username):
    """Получение пользователя по username"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,))
            return cursor.fetchone()
    except Exception as e:
        print(f"Error getting user: {e}")
        return None


def save_users_to_excel():
    """Экспорт в Excel"""
    try:
        users = get_all_users()
        if not users:
            return None

        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Пользователи"

        headers = [
            "ID", "Username", "Участие в квесте", "РТ СТАНЦИЯ", "ЛФИ СТАНЦИЯ",
            "ФАКТ СТАНЦИЯ", "ФЭФМ СТАНЦИЯ", "ФПМИ СТАНЦИЯ", "ФБМФ СТАНЦИЯ",
            "КНТ СТАНЦИЯ", "ФБВТ СТАНЦИЯ", "ВШПИ СТАНЦИЯ", "ВШМ СТАНЦИЯ",
            "ПИШ РПИ СТАНЦИЯ", "Количество пройденных станций",
            "Квест сумма баллов", "Квиз", "1", "2", "3", "4", "5"
        ]

        sheet.append(headers)
        for user in users:
            sheet.append(list(user))

        # Стилизация остаётся без изменений
        header_fill = PatternFill(start_color="4F81BD",
                                  end_color="4F81BD", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")

        for cell in sheet[1]:
            cell.fill = header_fill
            cell.font = header_font

        columns_to_highlight = [
            headers.index("Участие в квесте") + 1,
            headers.index("Квест сумма баллов") + 1,
            headers.index("Квиз") + 1
        ]

        column_fill = PatternFill(start_color="FFFF00",
                                  end_color="FFFF00", fill_type="solid")

        for row_idx in range(2, sheet.max_row + 1):
            for col_idx in columns_to_highlight:
                cell = sheet.cell(row=row_idx, column=col_idx)
                cell.fill = column_fill

        filename = "users.xlsx"
        workbook.save(filename)
        return filename
    except Exception as e:
        print(f"Error saving to Excel: {e}")
        return None


def get_all_users():
    """Получение всех пользователей"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM users")
            return cursor.fetchall()
    except Exception as e:
        print(f"Error getting all users: {e}")
        return []


def start_quest(username):
    """Старт квеста"""
    try:
        with db_manager.get_connection() as conn:
            conn.execute(
                "UPDATE users SET quest_started = 1 WHERE username = ?",
                (username,)
            )
            conn.commit()
    except Exception as e:
        print(f"Error starting quest: {e}")


def finish_quest(username):
    """Завершение квеста"""
    try:
        with db_manager.get_connection() as conn:
            conn.execute(
                "UPDATE users SET quest_station = 11 WHERE username = ?",
                (username,)
            )
            conn.commit()
    except Exception as e:
        print(f"Error finishing quest: {e}")


def is_quest_started(username):
    """Проверка старта квеста"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT quest_started FROM users WHERE username = ?",
                (username,)
            )
            result = cursor.fetchone()
            return result[0] == 1 if result else False
    except Exception as e:
        print(f"Error checking quest start: {e}")
        return False


def check_points(username):
    """Проверка баллов"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT quest_points FROM users WHERE username = ?",
                (username,)
            )
            result = cursor.fetchone()
            return result[0] if result else 0
    except Exception as e:
        print(f"Error checking points: {e}")
        return 0


def update_merch_points(username, points):
    """Обновление баллов мерча"""
    try:
        with db_manager.get_connection() as conn:
            conn.execute(
                "UPDATE users SET quest_points = quest_points - ? WHERE username = ?",
                (points, username)
            )
            conn.commit()
    except Exception as e:
        print(f"Error updating merch points: {e}")


def check_st_points(username, station):
    """Проверка баллов станции"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                f"SELECT quest{station}_points FROM users WHERE username = ?",
                (username,)
            )
            result = cursor.fetchone()
            return result[0] if result else 0
    except Exception as e:
        print(f"Error checking station points: {e}")
        return 0


def check_quiz_points(username, num):
    """Проверка баллов квиза"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                f"SELECT quize_{num} FROM users WHERE username = ?",
                (username,)
            )
            result = cursor.fetchone()
            return result[0] if result else 0
    except Exception as e:
        print(f"Error checking quiz points: {e}")
        return 0


def update_user_queststation(username):
    """Обновление статуса квеста"""
    try:
        with db_manager.get_connection() as conn:
            conn.execute("""
                UPDATE users SET quest_station = (
                    (quest1_points > 0) + (quest2_points > 0) + 
                    (quest3_points > 0) + (quest4_points > 0) + 
                    (quest5_points > 0) + (quest6_points > 0) + 
                    (quest7_points > 0) + (quest8_points > 0) + 
                    (quest9_points > 0) + (quest10_points > 0) + 
                    (quest11_points > 0)
                ) WHERE username = ?
            """, (username,))
            conn.commit()
    except Exception as e:
        print(f"Error updating quest station: {e}")


def is_quest_finished(username):
    """Проверка завершения квеста"""
    return is_got_any_merch(username)


def is_quiz_finished(username):
    """Проверка завершения квизов"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT quize_1, quize_2, quize_3, quize_4, quize_5
                FROM users WHERE username = ?
            """, (username,))
            result = cursor.fetchone()
            return all(score > 0 for score in result) if result else False
    except Exception as e:
        print(f"Error checking quiz completion: {e}")
        return False


def count_active_quests():
    """Подсчет активных квестов"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM users WHERE quest_started = 1"
            )
            return cursor.fetchone()[0]
    except Exception as e:
        print(f"Error counting active quests: {e}")
        return 0


def count_finished_quests():
    """Подсчет завершенных квестов"""
    try:
        users = get_all_users()
        return sum(is_got_any_merch(user[1]) for user in users)
    except Exception as e:
        print(f"Error counting finished quests: {e}")
        return 0


def update_user_points(username, admin_num, points):
    """Обновление баллов пользователя"""
    try:
        with db_manager.get_connection() as conn:
            conn.execute(
                f"UPDATE users SET quest{admin_num}_points = quest{admin_num}_points + ? WHERE username = ?",
                (points, username)
            )
            conn.execute(
                "UPDATE users SET quest_points = quest_points + ? WHERE username = ?",
                (points, username)
            )
            conn.commit()
    except Exception as e:
        print(f"Error updating user points: {e}")


def update_quize_points(username, num):
    """Обновление баллов квиза"""
    try:
        with db_manager.get_connection() as conn:
            conn.execute(
                f"UPDATE users SET quize_{num} = quize_{num} + 1 WHERE username = ?",
                (username,)
            )
            conn.execute(
                "UPDATE users SET quize_points = quize_points + 1 WHERE username = ?",
                (username,)
            )
            conn.commit()
    except Exception as e:
        print(f"Error updating quiz points: {e}")


def is_finished_quiz(username, num):
    """Проверка завершения квиза"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                f"SELECT quize_{num} FROM users WHERE username = ?",
                (username,)
            )
            result = cursor.fetchone()
            return result[0] > 0 if result else False
    except Exception as e:
        print(f"Error checking quiz finish: {e}")
        return False
