import openpyxl
from database import db_manager


def create_merch_table():
    """Создание таблицы мерча"""
    try:
        with db_manager.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS merch (
                    username TEXT UNIQUE,
                    "Раскрасить футболку" INTEGER DEFAULT 0,
                    "Раскрасить шоппер" INTEGER DEFAULT 0,
                    "Футболка" INTEGER DEFAULT 0,
                    "Блокнот" INTEGER DEFAULT 0,
                    "ПБ" INTEGER DEFAULT 0
                )
            """)
            conn.commit()
    except Exception as e:
        print(f"Error creating merch table: {e}")


def got_merch(username, merch_type):
    """Проверка наличия мерча"""
    try:
        with db_manager.get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO merch (username) VALUES (?)", (username,))
            conn.commit()
            cursor = conn.execute(
                f'SELECT "{merch_type}" FROM merch WHERE username = ?',
                (username,)
            )
            result = cursor.fetchone()
            return result[0] == 1 if result else False
    except Exception as e:
        print(f"Error checking merch: {e}")
        return False


def give_merch(username, merch_type):
    try:
        with db_manager.get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO merch (username) VALUES (?)", (username,))
            conn.commit()
            conn.execute(
                f'UPDATE merch SET "{merch_type}" = 1 WHERE username = ?',
                (username,)
            )
            conn.commit()
    except Exception as e:
        print(f"Error giving merch: {e}")


def is_got_merch(username):
    try:
        with db_manager.get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO merch (username) VALUES (?)", (username,))
            conn.commit()
            cursor = conn.execute("PRAGMA table_info(merch);")
            columns = [col[1] for col in cursor.fetchall()]

            numeric_columns = [
                col for col in columns
                if col != 'username'
            ]

            if not numeric_columns:
                return False

            sum_query = " + ".join([f'"{col}"' for col in numeric_columns])
            cursor = conn.execute(
                f"SELECT {sum_query} FROM merch WHERE username = ?",
                (username,)
            )
            result = cursor.fetchone()
            return (result[0] == len(numeric_columns)) if result else False
    except Exception as e:
        print(f"Error checking full merch: {e}")
        return False


def is_got_any_merch(username):
    try:
        with db_manager.get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO merch (username) VALUES (?)", (username,))
            conn.commit()
            cursor = conn.execute("PRAGMA table_info(merch);")
            columns = [col[1] for col in cursor.fetchall()]

            numeric_columns = [
                col for col in columns
                if col != 'username'
            ]

            if not numeric_columns:
                return False

            sum_query = " + ".join([f'"{col}"' for col in numeric_columns])
            cursor = conn.execute(
                f"SELECT {sum_query} FROM merch WHERE username = ?",
                (username,)
            )
            result = cursor.fetchone()
            return (result[0] > 0) if result else False
    except Exception as e:
        print(f"Error checking any merch: {e}")
        return False


def add_column(column_name):
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute("PRAGMA table_info(merch);")
            existing_columns = [row[1] for row in cursor.fetchall()]

            if column_name not in existing_columns:
                conn.execute(
                    f"ALTER TABLE merch ADD COLUMN \"{column_name}\" INTEGER DEFAULT 0")
                conn.commit()
                print(f"Column '{column_name}' added")
            else:
                print(f"Column '{column_name}' already exists")
    except Exception as e:
        print(f"Error adding column: {e}")


def get_all_merch():
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM merch")
            return cursor.fetchall()
    except Exception as e:
        print(f"Error getting merch data: {e}")
        return []


def get_table_columns(table_name):
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute(f"PRAGMA table_info({table_name});")
            return [column[1] for column in cursor.fetchall()]
    except Exception as e:
        print(f"Error getting table columns: {e}")
        return []


def save_merch_to_excel():
    try:
        merch_data = get_all_merch()
        columns = get_table_columns('merch')

        if not merch_data:
            return None

        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Мерч"

        sheet.append(columns)
        for item in merch_data:
            sheet.append(list(item))

        filename = "merch.xlsx"
        workbook.save(filename)
        return filename
    except Exception as e:
        print(f"Error saving to Excel: {e}")
        return None
