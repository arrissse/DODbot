from bot import bot
import sqlite3
from telebot import types
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboard import main_keyboard, pro_admin_merch, pro_admin_keyboard, pro_admin_quiz_start
from users import save_users_to_excel, count_active_quests, get_user_by_username
from users import count_finished_quests
from users import check_points, update_merch_points
from admin import save_admins_to_excel, get_admin_by_username, get_admin_level
from merch import give_merch, is_got_merch, got_merch, add_column, save_merch_to_excel
from quiz import quiz_schedule


'''
-----------------------

admins

-----------------------
'''


@bot.message_handler(commands=["admins"])
def send_admins_list(message):

    user = get_admin_by_username('@' + message.from_user.username)
    level = get_admin_level('@' + message.from_user.username)

    if user and level == 0:
        filename = save_admins_to_excel()
        print(f"Файл Excel создан: {filename}")

        if filename:
            with open(filename, "rb") as file:
                bot.send_document(message.chat.id, file)
        else:
            bot.send_message(
                message.chat.id, "❌ В базе данных нет пользователей.")
    else:
        bot.send_message(
            message.chat.id, "❌ У вас нет доступа к этой команде.")


'''
-----------------------

merch

-----------------------
'''


@bot.message_handler(commands=["merch"])
def send_admins_list(message):

    user = get_admin_by_username('@' + message.from_user.username)
    level = get_admin_level('@' + message.from_user.username)

    if user and level == 0:
        filename = save_merch_to_excel()
        print(f"Файл Excel создан: {filename}")

        if filename:
            with open(filename, "rb") as file:
                bot.send_document(message.chat.id, file)
        else:
            bot.send_message(message.chat.id, "❌ База данных пуста.")
    else:
        bot.send_message(
            message.chat.id, "❌ У вас нет доступа к этой команде.")


'''
-----------------------

Мерч

-----------------------
'''


@bot.message_handler(func=lambda message: message.text == "Мерч")
def pro_admin_merch_button(message):
    user = get_admin_by_username('@' + message.from_user.username)
    level = get_admin_level('@' + message.from_user.username)

    try:
        if user and level == 0:
            bot.send_message(message.chat.id, "Выберите действие:",
                             reply_markup=pro_admin_merch())
        else:
            bot.send_message(
                message.chat.id, "❌ У вас нет доступа к этой команде.")
    except Exception as e:
        bot.send_message(message.chat.id, e)


'''
-----------------------

Назад

-----------------------
'''


@bot.message_handler(func=lambda message: message.text == "Назад ⬅️")
def pro_admin_merch_back(message):
    user = get_admin_by_username('@' + message.from_user.username)
    level = get_admin_level('@' + message.from_user.username)
    try:
        if user and level == 0:
            bot.send_message(message.chat.id, "🔑 Админ-меню:",
                             reply_markup=pro_admin_keyboard())
        else:
            bot.send_message(
                message.chat.id, "❌ У вас нет доступа к этой команде.")
    except Exception as e:
        bot.send_message(message.chat.id, e)


'''
-----------------------

Начать квиз

-----------------------
'''


@bot.message_handler(func=lambda message: message.text == "Начать квиз")
def pro_admin_quiz_button(message):
    user = get_admin_by_username('@' + message.from_user.username)
    level = get_admin_level('@' + message.from_user.username)

    try:
        if user and level == 0:
            bot.send_message(message.chat.id, "Выберите квиз:",
                             reply_markup=pro_admin_quiz_start())
        else:
            bot.send_message(
                message.chat.id, "❌ У вас нет доступа к этой команде.")
    except Exception as e:
        bot.send_message(message.chat.id, e)


quiz_list = {
    "Квиз 1": 1,
    "Квиз 2": 2,
    "Квиз 3": 3,
    "Квиз 4": 4,
    "Квиз 5": 5,
}


@bot.message_handler(func=lambda message: message.text in quiz_list)
def handle_quiz_start(message):
    quiz_number = quiz_list[message.text]
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Да", callback_data=f'start_quiz:{quiz_number}:'), InlineKeyboardButton(
        "Нет", callback_data=f'not_start_quiz:'), )
    bot.send_message(message.chat.id, f"Начать {message.text}?")


@bot.callback_query_handler(func=lambda call: call.data.startswith("start_quiz:"))
def start_quiz(call):
    bot.answer_callback_query(call.id)
    try:
        _, quiz_number_str = call.data.split(":")
        quiz_number = int(quiz_number_str)
    except ValueError as e:
        bot.send_message(call.message.chat.id,
                         f"Ошибка при извлечении номера квиза: {e}")
        return

    current_time = datetime.now().strftime("%H:%M")
    quiz_times = sorted(quiz_schedule.keys())
    if quiz_number > len(quiz_times):
        bot.send_message(call.message.chat.id,
                         "Ошибка: квиз с таким номером не найден.")
        return
    selected_time = quiz_times[quiz_number - 1]
    quiz_info = quiz_schedule[selected_time]
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Отправить следующий вопрос", callback_data=f'next_question:{quiz_number}:'))
    bot.send_message(call.message.chat.id,
                     f"✅ {quiz_info[0]} начат!", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "not_start_quiz")
def cancel_quiz(call):
    bot.answer_callback_query(call.id, "❌ Операция отменена.")
    bot.send_message(call.message.chat.id, "❌ Операция отменена.")


'''
-----------------------

Таблица пользователей

-----------------------
'''


@bot.message_handler(func=lambda message: message.text == "Таблица пользователей")
def send_users_list(message):
    user = get_admin_by_username('@' + message.from_user.username)
    if user:
        filename = save_users_to_excel()

        if filename:
            with open(filename, "rb") as file:
                bot.send_document(message.chat.id, file)
    else:
        bot.send_message(message.chat.id, "❌ В базе данных нет пользователей.")


'''
-----------------------

Переключить меню

-----------------------
'''


@bot.message_handler(func=lambda message: message.text == "Переключить меню")
def chage_menu(m):
    bot.send_message(m.chat.id, "Для повторного переключения меню введите /start",
                     reply_markup=main_keyboard())


'''
-----------------------

Квест. Текущая статистика

-----------------------
'''


@bot.message_handler(func=lambda message: message.text == "Квест. Текущая статистика")
def statistics(message):
    user = get_admin_by_username('@' + message.from_user.username)
    if user:
        active_users = count_active_quests()
        finished_users = count_finished_quests()
        bot.send_message(
            message.chat.id, f"Количество пользователей, начавших квест: {active_users}\n"
            f"Количество пользователей, завершивших квест: {finished_users}\n")
    else:
        bot.send_message(
            message.chat.id, "❌ У вас нет доступа к этой команде.")


'''
-----------------------

Стоимость мерча

-----------------------
'''


def create_price_table():
    conn = sqlite3.connect("merch.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS merch_prices (
        merch_type TEXT PRIMARY KEY,
        price INTEGER DEFAULT 0
    )
    """)
    cursor.execute("""
    INSERT OR IGNORE INTO merch_prices (merch_type, price) VALUES 
        ("Раскрасить футболку", 7),
        ("Раскрасить шоппер", 5),
        ("Футболка", 8),
        ("Блокнот", 2),
        ("ПБ", 15);
    """)

    conn.commit()
    conn.close()


def get_merch_types():
    conn = sqlite3.connect("merch.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT merch_type FROM merch_prices")
    types = [row[0] for row in cursor.fetchall()]
    conn.close()
    return types


def get_merch_price(merch_type):
    conn = sqlite3.connect("merch.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT price FROM merch_prices WHERE merch_type = ?", (merch_type,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0


def update_merch_price(merch_type, new_price):
    conn = sqlite3.connect("merch.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO merch_prices (merch_type, price) VALUES (?, ?) ON CONFLICT(merch_type) DO UPDATE SET price = ?",
                   (merch_type, new_price, new_price))
    conn.commit()
    conn.close()


@bot.message_handler(func=lambda message: message.text == "Стоимость мерча")
def merch_prices_menu(message):
    conn = sqlite3.connect("merch.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT merch_type FROM merch_prices")
    merch_types = [row[0] for row in cursor.fetchall()]
    conn.close()

    markup = types.InlineKeyboardMarkup()
    for merch in merch_types:
        markup.add(types.InlineKeyboardButton(
            merch, callback_data=f"edit_price:{merch}"))

    bot.send_message(
        message.chat.id, "Выберите товар для изменения стоимости:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_price"))
def edit_price(call):
    merch_type = call.data.split(":")[1]
    current_price = get_merch_price(merch_type)
    bot.send_message(call.message.chat.id,
                     f"Текущая стоимость {merch_type}: {current_price}\nВведите новую стоимость:")
    bot.register_next_step_handler(
        call.message, lambda msg: process_new_price(msg, merch_type))


def process_new_price(message, merch_type):
    try:
        new_price = int(message.text)
        update_merch_price(merch_type, new_price)
        bot.send_message(
            message.chat.id, f"✅ Стоимость {merch_type} обновлена до {new_price}!")
    except ValueError:
        bot.send_message(
            message.chat.id, "❌ Ошибка! Введите корректное число.")


'''
-----------------------

Выдать мерч

-----------------------
'''


@bot.message_handler(func=lambda message: message.text == "Выдать мерч")
def give_merch_to_user(message):
    user = get_admin_by_username('@' + message.from_user.username)
    if user and (user[1] == 0 or user[1] == 1):
        bot.send_message(
            message.chat.id, "Введите ник пользователя (@username):")
        bot.register_next_step_handler(message, process_fusername)
    else:
        bot.send_message(
            message.chat.id, "❌ У вас нет доступа к этой команде.")


def process_fusername(m):
    try:
        if m.text[0] != '@':
            bot.send_message(
                m.chat.id, f"❌ Введите корректно ник пользователя.")
            return
        username = m.text.lstrip('@')
        if is_got_merch(username):
            bot.send_message(
                m.chat.id, f"❌ Пользователь {username} уже получил мерч.")
            return
        if not get_user_by_username(username):
            bot.send_message(
                m.chat.id, f"❌ Пользователя {username} нет в базе.")
            return

        markup = InlineKeyboardMarkup()

        merch_types = get_merch_types()
        for merch in merch_types:
            if check_points(username) >= get_merch_price(merch) and not got_merch(username, merch.lower()):
                markup.add(InlineKeyboardButton(
                    merch, callback_data=f'give_merch:{get_merch_price(merch)}:{merch.lower()}:{username}'))

        if markup.keyboard:
            bot.send_message(
                m.chat.id, f"Выберите мерч пользователю {username}:", reply_markup=markup)
        else:
            bot.send_message(
                m.chat.id, f"❌ Пользователь {username} не может получить мерч.")
    except Exception as e:
        bot.send_message(m.chat.id, e)


@bot.callback_query_handler(func=lambda call: call.data.startswith("give_merch"))
def process_merch_callback(call):
    _, merch_price, merch_type, username = call.data.split(":")

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(
            'Да', callback_data=f'yes:{merch_price}:{merch_type}:{username}'),
        InlineKeyboardButton('Нет', callback_data='no')
    )
    bot.send_message(call.message.chat.id,
                     f"Выдать {username} {merch_type}?", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("yes"))
def process_merch_call_yes(call):
    _, merch_price, merch_type, username = call.data.split(":")
    give_merch(username, merch_type)
    update_merch_points(username, merch_price)
    print(int(get_merch_price(merch_type)))
    bot.answer_callback_query(call.id, "✅ Мерч за квест выдан!")
    bot.send_message(call.message.chat.id,
                     f"✅ Пользователю {username} выдан мерч за квест!")


@bot.callback_query_handler(func=lambda call: call.data.startswith("no"))
def process_merch_call_no(call):
    bot.answer_callback_query(call.id, "❌ Операция отменена.")
    bot.send_message(call.message.chat.id, "❌ Операция отменена.")


'''
-----------------------

Добавить позицию мерча

-----------------------
'''


@bot.message_handler(func=lambda message: message.text == "Добавить позицию мерча")
def add_merch_type(message):
    user = get_admin_by_username('@' + message.from_user.username)
    if user and user[1] == 0:
        bot.send_message(
            message.chat.id, "Введите название новой позиции мерча: ")
        bot.register_next_step_handler(message, process_type)
    else:
        bot.send_message(
            message.chat.id, "❌ У вас нет доступа к этой команде.")


def process_type(message):
    type = message.text
    bot.send_message(
        message.chat.id, "Введите стоимость новой позиции мерча: ")
    bot.register_next_step_handler(
        message, lambda msg: process_type_cost(msg, type))


def process_type_cost(message, type):
    try:
        cost = int(message.text)
    except ValueError:
        bot.send_message(
            message.chat.id, "❌ Стоимость должна быть числом. Попробуйте ещё раз.")
        return
    conn = sqlite3.connect("merch.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO merch_prices (merch_type, price) VALUES (?, ?)
    """, (type, cost))

    conn.commit()
    conn.close()

    try:
        add_column(type)
    except Exception as e:
        bot.send_message(
            message.chat.id, f"❌ Ошибка при добавлении колонки: {e}")

    bot.send_message(
        message.chat.id, f"✅ Позиция '{type}' добавлена с ценой {cost} баллов.")


'''
-----------------------

Удалить позицию мерча

-----------------------
'''


@bot.message_handler(func=lambda message: message.text == "Удалить позицию мерча")
def remove_merch_type(message):
    user = get_admin_by_username('@' + message.from_user.username)
    if user and user[1] == 0:
        bot.send_message(
            message.chat.id, "Введите название позиции мерча, которую необходимо удалить: ")
        bot.register_next_step_handler(message, process_r_type)
    else:
        bot.send_message(
            message.chat.id, "❌ У вас нет доступа к этой команде.")


def process_r_type(message):
    merch_type = message.text.strip()

    conn = sqlite3.connect("merch.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM merch_prices WHERE merch_type = ?", (merch_type,))
    if cursor.fetchone()[0] == 0:
        bot.send_message(
            message.chat.id, f"❌ Позиция '{merch_type}' не найдена.")
        conn.close()
        return

    cursor.execute(
        "DELETE FROM merch_prices WHERE merch_type = ?", (merch_type,))

    cursor.execute("PRAGMA table_info(merch);")
    columns = [row[1] for row in cursor.fetchall()]

    if merch_type in columns:
        new_columns = [col for col in columns if col != merch_type]
        if not new_columns:
            bot.send_message(
                message.chat.id, "❌ Ошибка: нельзя удалить последнюю колонку.")
            conn.close()
            return

        columns_str = ", ".join(f'"{col}"' for col in new_columns)

        cursor.execute(
            f"CREATE TABLE merch_temp AS SELECT {columns_str} FROM merch;")
        cursor.execute("DROP TABLE merch;")
        cursor.execute("ALTER TABLE merch_temp RENAME TO merch;")

    conn.commit()
    conn.close()

    bot.send_message(message.chat.id, f"✅ Позиция '{merch_type}' удалена.")
