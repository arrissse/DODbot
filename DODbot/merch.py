import sqlite3
import openpyxl
from bot import bot

def create_merch_table():
    conn = sqlite3.connect("merch.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS merch (
            username TEXT,            -- Имя пользователя (@username)
            pshirt INTEGER DEFAULT 0, -- раскрасить футболку (7)
            pshopper INTEGER DEFAULT 0, -- раскрасить шоппер (5)
            shirt INTEGER DEFAULT 0, -- получить футболку (8)
            notebook INTEGER DEFAULT 0, -- блокнот (2)
            pb INTEGER DEFAULT 0 -- ПБ (15)
    )
    """)

create_merch_table()

def got_merch(username, type):
    conn = sqlite3.connect("merch.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO merch (username) VALUES (?)",
                   (username,))
    cursor.execute(
        f"SELECT {type} FROM merch WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()

    return result[0] == 1

def give_merch(username, type):
    conn = sqlite3.connect("merch.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO merch (username) VALUES (?)",
                   (username,))
    cursor.execute(
        f"UPDATE merch SET {type} = 1 WHERE username = ?", (username,))
    conn.commit()
    conn.close()

def is_got_merch(username):
    conn = sqlite3.connect("merch.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO merch (username) VALUES (?)",
                   (username,))
    query = """
        SELECT 
            COALESCE(pshirt, 0) +
            COALESCE(pshopper, 0) +
            COALESCE(shirt, 0) +
            COALESCE(notebook, 0) +
            COALESCE(pb, 0)
        FROM merch
        WHERE username = ?
    """
    cursor.execute(query, (username,))
    result = cursor.fetchone()
    conn.close()
    return result[0] == 5

def is_got_any_merch(username):
    conn = sqlite3.connect("merch.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO merch (username) VALUES (?)",
                   (username,))
    query = """
        SELECT 
            COALESCE(pshirt, 0) +
            COALESCE(pshopper, 0) +
            COALESCE(shirt, 0) +
            COALESCE(notebook, 0) +
            COALESCE(pb, 0)
        FROM merch
        WHERE username = ?
    """
    cursor.execute(query, (username,))
    result = cursor.fetchone()
    conn.close()
    return result[0] > 0