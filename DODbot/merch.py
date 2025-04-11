import sqlite3
import openpyxl
from bot import bot
from database import db_lock, get_connection


def create_merch_table():
    with db_lock:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
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


def got_merch(username, type):
    with db_lock:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO merch (username) VALUES (?)", (username,))
            cursor.execute(
                f'SELECT "{type}" FROM merch WHERE username = ?', (username,))
            result = cursor.fetchone()
            return result[0] == 1 if result else False


def give_merch(username, type):
    with db_lock:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO merch (username) VALUES (?)", (username,))
            cursor.execute(
                f'UPDATE merch SET "{type}" = 1 WHERE username = ?', (username,))
            conn.commit()


def is_got_merch(username):
    with db_lock:
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "INSERT OR IGNORE INTO merch (username) VALUES (?)", (username,))

            cursor.execute("PRAGMA table_info(merch);")
            columns = cursor.fetchall()

            numeric_columns = [col[1] for col in columns if col[1]
                               != 'username' and col[2] in ('INTEGER', 'REAL')]

            if not numeric_columns:
                
                return False

            sum_query = " + ".join(
                [f'COALESCE("{col}", 0)' for col in numeric_columns])

            query = f"SELECT {sum_query} FROM merch WHERE username = ?"
            cursor.execute(query, (username,))

            result = cursor.fetchone()
            

            return result[0] == len(numeric_columns)


def is_got_any_merch(username):
    conn = sqlite3.connect("merch.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO merch (username) VALUES (?)", (username,))

    cursor.execute("PRAGMA table_info(merch);")
    columns = cursor.fetchall()

    numeric_columns = [col[1] for col in columns if col[1] !=
                       'username' and col[2] and col[2].upper() in ('INTEGER', 'REAL')]

    if not numeric_columns:
        
        return False

    sum_query = " + ".join([f"COALESCE({col}, 0)" for col in numeric_columns])

    query = f"SELECT {sum_query} FROM merch WHERE username = ?"
    cursor.execute(query, (username,))

    result = cursor.fetchone()
    

    return result and result[0] > 0


def add_column(column_name):
    with db_lock:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(merch);")
            existing_columns = [row[1] for row in cursor.fetchall()]

            if column_name not in existing_columns:
                cursor.execute(
                    f"ALTER TABLE merch ADD COLUMN '{column_name}' INTEGER DEFAULT 0")
                conn.commit()


def get_all_merch():
    with db_lock:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM merch")
            merch = cursor.fetchall()
            
            return [(merch_) for merch_ in merch]


def get_table_columns(table_name):
    with db_lock:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = [column[1] for column in cursor.fetchall()]
            
            return columns


def save_merch_to_excel():
    merch = get_all_merch()
    columns = get_table_columns('merch')

    if not merch:
        return None

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Мерч"

    sheet.append(columns)

    for merch_ in merch:
        sheet.append(list(merch_))

    filename = "merch.xlsx"
    workbook.save(filename)
    return filename
