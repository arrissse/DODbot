import sqlite3
import openpyxl
from bot import bot

def create_merch_table():
    conn = sqlite3.connect("merch.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS merch (
            username TEXT UNIQUE,                 -- Имя пользователя (@username)
            "Раскрасить футболку" INTEGER DEFAULT 0,  -- раскрасить футболку (7)
            "Раскрасить шоппер" INTEGER DEFAULT 0,   -- раскрасить шоппер (5)
            "Футболка" INTEGER DEFAULT 0,           -- получить футболку (8)
            "Блокнот" INTEGER DEFAULT 0,           -- блокнот (2)
            "ПБ" INTEGER DEFAULT 0                 -- ПБ (15)
        )
    """)


def got_merch(username, type):
    conn = sqlite3.connect("merch.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO merch (username) VALUES (?)",
                   (username,))
    cursor.execute(
        f'SELECT "{type}" FROM merch WHERE username = ?', (username,))
    result = cursor.fetchone()
    conn.close()

    return result[0] == 1

def give_merch(username, type):
    conn = sqlite3.connect("merch.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO merch (username) VALUES (?)",
                   (username,))
    cursor.execute(
        f'UPDATE merch SET "{type}" = 1 WHERE username = ?', (username,))
    conn.commit()
    conn.close()

def is_got_merch(username):
    conn = sqlite3.connect("merch.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("INSERT OR IGNORE INTO merch (username) VALUES (?)", (username,))

    cursor.execute("PRAGMA table_info(merch);")
    columns = cursor.fetchall()

    numeric_columns = [col[1] for col in columns if col[1] != 'username' and col[2] in ('INTEGER', 'REAL')]

    if not numeric_columns:
        conn.close()
        return False  

    sum_query = " + ".join([f'COALESCE("{col}", 0)' for col in numeric_columns])

    query = f"SELECT {sum_query} FROM merch WHERE username = ?"
    cursor.execute(query, (username,))
    
    result = cursor.fetchone()
    conn.close()

    return result[0] == len(numeric_columns)


def is_got_any_merch(username):
    conn = sqlite3.connect("merch.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("INSERT OR IGNORE INTO merch (username) VALUES (?)", (username,))

    cursor.execute("PRAGMA table_info(merch);")
    columns = cursor.fetchall()

    numeric_columns = [col[1] for col in columns if col[1] != 'username' and col[2] in ('INTEGER', 'REAL')]

    sum_query = " + ".join([f"COALESCE({col}, 0)" for col in numeric_columns])

    query = f"SELECT {sum_query} FROM merch WHERE username = ?"
    cursor.execute(query, (username,))
    
    result = cursor.fetchone()
    conn.close()
    
    return result[0] > 0 if result else False

def add_column(column_name, column_type="INTEGER DEFAULT 0"):
    conn = sqlite3.connect("merch.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(merch);")
    existing_columns = [row[1] for row in cursor.fetchall()]

    if column_name not in existing_columns:
        cursor.execute(f"ALTER TABLE merch ADD COLUMN {column_name} {column_type};")
        conn.commit()
        print(f"Столбец '{column_name}' добавлен в таблицу.")
    else:
        print(f"Столбец '{column_name}' уже существует.")

    conn.close()

def get_all_merch():
    conn = sqlite3.connect("merch.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM merch")
    merch = cursor.fetchall()
    conn.close()
    return [(merch_) for merch_ in merch]


def get_table_columns(table_name):
    conn = sqlite3.connect("merch.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = [column[1] for column in cursor.fetchall()]
    conn.close()
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