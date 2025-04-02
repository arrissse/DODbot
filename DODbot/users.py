import sqlite3
import openpyxl
from openpyxl.styles import Font, PatternFill
from merch import is_got_any_merch


def create_users_table():
    conn = sqlite3.connect("users.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,   -- Telegram ID (уникальный)
            username TEXT,            -- Имя пользователя (@username)
            quest_started INTEGER DEFAULT 0, -- Начал ли пользователь квест (0 - нет, 1 - да)
            quest1_points INTEGER DEFAULT 0,  -- Баллы за РТ
            quest2_points INTEGER DEFAULT 0,  -- Баллы за ЛФИ
            quest3_points INTEGER DEFAULT 0,  -- Баллы за ФАКТ
            quest4_points INTEGER DEFAULT 0,  -- Баллы за ФЭФМ
            quest5_points INTEGER DEFAULT 0,   -- Баллы за ФПМИ
            quest6_points INTEGER DEFAULT 0,   -- Баллы за ФБМФ
            quest7_points INTEGER DEFAULT 0,   -- Баллы за КНТ
            quest8_points INTEGER DEFAULT 0,   -- Баллы за ФБВТ
            quest9_points INTEGER DEFAULT 0,   -- Баллы за ВШПИ
            quest10_points INTEGER DEFAULT 0,   -- Баллы за ВШМ
            quest11_points INTEGER DEFAULT 0,   -- Баллы за ПИШ РПИ
            quest_station INTEGER DEFAULT 0,   -- Количество пройденных станций
            quest_points INTEGER DEFAULT 0,  -- Баллы за квест
            quize_points INTEGER DEFAULT 0,  -- Баллы за квиз
            quize_1 INTEGER DEFAULT 0,  -- Баллы за квиз 1
            quize_2 INTEGER DEFAULT 0,  -- Баллы за квиз 2
            quize_3 INTEGER DEFAULT 0,  -- Баллы за квиз 3
            quize_4 INTEGER DEFAULT 0,  -- Баллы за квиз 4
            quize_5 INTEGER DEFAULT 0  -- Баллы за квиз 5
    )
    """)
    conn.commit()
    conn.close()


'''
-----------------------

Добавить пользователя

-----------------------
'''
def add_user(user_id, username):
    conn = sqlite3.connect("users.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)",
                   (user_id, username))
    conn.commit()
    conn.close()


'''
-----------------------

Получить данные о user по его нику

-----------------------
'''
def get_user_by_username(username):
    conn = sqlite3.connect("users.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user if user else None


'''
-----------------------

Таблица пользователей

-----------------------
'''
def save_users_to_excel():
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
        "ПИШ РПИ СТАНЦИЯ", "Количество пройденных станций", "Квест сумма баллов", "Квиз", "1", "2", "3", "4", "5"
    ]

    sheet.append(headers)

    for user in users:
        sheet.append(list(user))

    header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")

    for cell in sheet[1]:
        cell.fill = header_fill
        cell.font = header_font

    columns_to_highlight = [
        headers.index("Участие в квесте") + 1,  
        headers.index("Квест сумма баллов") + 1,  
        headers.index("Квиз") + 1  
    ]

    column_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")

    for row_idx in range(2, sheet.max_row + 1):
        for col_idx in columns_to_highlight:
            cell = sheet.cell(row=row_idx, column=col_idx)
            cell.fill = column_fill

    filename = "users.xlsx"
    workbook.save(filename)
    return filename



'''
-----------------------

Все пользователи

-----------------------
'''
def get_all_users():
    conn = sqlite3.connect("users.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    return users


'''
-----------------------

Начать квест

-----------------------
'''
def start_quest(username):
    conn = sqlite3.connect("users.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET quest_started = 1 WHERE username = ?", (username,))
    conn.commit()
    conn.close()


'''
-----------------------

Завершить квест

-----------------------
'''
def finish_quest(username):
    conn = sqlite3.connect("users.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET quest_station = 11 WHERE username = ?", (username,))
    conn.commit()
    conn.close()


'''
-----------------------

Начат ли квест

-----------------------
'''

def is_quest_started(username):
    conn = sqlite3.connect("users.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT quest_started FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()

    return result[0] == 1


'''
-----------------------

Баллы за квест

-----------------------
'''
def check_points(username):
    conn = sqlite3.connect("users.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT quest_points FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()

    return result[0]


'''
-----------------------

Изменить сумму баллов за квест

-----------------------
'''
def update_merch_points(username, points):
    conn = sqlite3.connect("users.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
    if cursor.fetchone()[0] == 0:
        print(f"❌ Пользователь {username} не найден в users.db!")
        conn.close()
        return
    
    cursor.execute(
        "SELECT quest_points FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    if result:
        current_points = result[0]
        updated_points = current_points - int(points)

        cursor.execute(
            "UPDATE users SET quest_points = ? WHERE username = ?", 
            (updated_points, username)
        )

        conn.commit()
    else:
        print(f"❌ Не удалось получить баллы для пользователя {username}")

    conn.close()


'''
-----------------------

Баллы за станцию

-----------------------
'''
def check_st_points(username, station):
    conn = sqlite3.connect("users.db", check_same_thread=False)
    cursor = conn.cursor()

    s = f"quest{station}_points"
    cursor.execute(
        f"SELECT {s} FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()

    return result[0]

'''
-----------------------

Баллы за квиз

-----------------------
'''

def check_quiz_points(username, num):
    conn = sqlite3.connect("users.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute(
        f"SELECT quize_{num} FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()

    return result[0]


'''
-----------------------

Обновить количество пройденных станций

-----------------------
'''

def update_user_queststation(username):
    conn = sqlite3.connect("users.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users 
        SET quest_station = (
            (quest1_points > 0) +
            (quest2_points > 0) +
            (quest3_points > 0) +
            (quest4_points > 0) +
            (quest5_points > 0) +
            (quest6_points > 0) +
            (quest7_points > 0) +
            (quest8_points > 0) +
            (quest9_points > 0) +
            (quest10_points > 0) +
            (quest11_points > 0)
        )
        WHERE username = ?
    """, (username,))

    conn.commit()
    conn.close()


'''
-----------------------

Завершён ли квест

-----------------------
'''
def is_quest_finished(username):
    return is_got_any_merch(username)


'''
-----------------------

Завершен ли квмз

-----------------------
'''
def is_quiz_finished(username):
    conn = sqlite3.connect("users.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT quize_1, quize_2, quize_3, quize_4, quize_5
        FROM users WHERE username = ?
    """, (username,))
    
    result = cursor.fetchone()
    conn.close()

    return result is not None and all(score > 0 for score in result)




'''
-----------------------

Количество начавших квест

-----------------------
'''

def count_active_quests():
    conn = sqlite3.connect("users.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users WHERE quest_started = 1")
    result = cursor.fetchone()[0]
    conn.close()

    return result


'''
-----------------------

Количество завершивших квест

-----------------------
'''

def count_finished_quests():
    result = 0
    users = get_all_users()
    for user in users:
        result += is_got_any_merch(user[1])
    return result


'''
-----------------------

Проставить баллы за квест

-----------------------
'''
def update_user_points(username, admin_num, points):
    conn = sqlite3.connect("users.db", check_same_thread=False)
    cursor = conn.cursor()

    column_name = f"quest{admin_num}_points"
    query = f"UPDATE users SET {column_name} = {column_name} + ? WHERE username = ?"
    cursor.execute(query, (points, username))

    query = "UPDATE users SET quest_points = quest_points + ? WHERE username = ?"
    cursor.execute(query, (points, username))

    conn.commit()
    conn.close()


'''
-----------------------

Обновить баллы за квиз

-----------------------
'''

def update_quize_points(username, num):
    conn = sqlite3.connect("users.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT quize_points FROM users WHERE username = ?", (username,))

    column_name = f"quize_{num}"
    query = f"UPDATE users SET {column_name} = {column_name} + ? WHERE username = ?"
    cursor.execute(query, (1, username))

    query = "UPDATE users SET quize_points = quize_points + 1 WHERE username = ?"
    cursor.execute(query, (username,))
    print(f"Баллы обновлены для {username}")

    conn.commit()
    conn.close()


'''
-----------------------

Баллы за определенный квиз

-----------------------
'''
def check_quiz_points(username, num):
    conn = sqlite3.connect("users.db", check_same_thread=False)
    cursor = conn.cursor()

    quize = f"quize_{num}"

    cursor.execute(
        f"SELECT {quize} FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()

    if result is None:
        return False

    return result[0]



'''
-----------------------

Пройден ли был определённый квиз

-----------------------
'''
def is_finished_quiz(username, num):
    conn = sqlite3.connect("users.db", check_same_thread=False)
    cursor = conn.cursor()

    quize = f"quize_{num}"

    cursor.execute(
        f"SELECT {quize} FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()

    if result is None:
        return False

    return result[0] > 0


