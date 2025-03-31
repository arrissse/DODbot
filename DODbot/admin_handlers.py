from bot import bot
import sqlite3
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboard import main_keyboard
from users import save_users_to_excel, count_active_quests, get_user_by_username
from users import count_finished_quests, is_quest_finished, finish_quest, update_user_queststation, is_quiz_finished
from users import check_points, update_merch_points
from admin import save_admins_to_excel, get_admin_by_username, get_admin_level
from merch import give_merch, is_got_merch, got_merch

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
            bot.send_message(message.chat.id, "❌ В базе данных нет пользователей.")
    else:
        bot.send_message(message.chat.id, "❌ У вас нет доступа к этой команде.")


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
        bot.send_message(message.chat.id, "❌ У вас нет доступа к этой команде.")
    
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
        ('Раскрасить футболку', 7),
        ('Раскрасить шоппер', 5),
        ('Футболка', 8),
        ('Блокнот', 2),
        ('ПБ', 15);
    """)

    conn.commit()
    conn.close()

create_price_table()

def get_merch_price(merch_type):
    conn = sqlite3.connect("merch.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT price FROM merch_prices WHERE merch_type = ?", (merch_type,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def update_merch_price(merch_type, new_price):
    conn = sqlite3.connect("merch.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO merch_prices (merch_type, price) VALUES (?, ?) ON CONFLICT(merch_type) DO UPDATE SET price = ?", (merch_type, new_price, new_price))
    conn.commit()
    conn.close()

@bot.message_handler(func=lambda message: message.text == "Стоимость мерча")
def merch_prices_menu(message):
    markup = types.InlineKeyboardMarkup()
    for merch in ["Раскрасить футболку", "Раскрасить шоппер", "Футболка", "Блокнот", "ПБ"]:
        markup.add(types.InlineKeyboardButton(merch, callback_data=f"edit_price:{merch}"))
    bot.send_message(message.chat.id, "Выберите товар для изменения стоимости:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_price"))
def edit_price(call):
    merch_type = call.data.split(":")[1]
    current_price = get_merch_price(merch_type)
    bot.send_message(call.message.chat.id, f"Текущая стоимость {merch_type}: {current_price}\nВведите новую стоимость:")
    bot.register_next_step_handler(call.message, lambda msg: process_new_price(msg, merch_type))

def process_new_price(message, merch_type):
    try:
        new_price = int(message.text)
        update_merch_price(merch_type, new_price)
        bot.send_message(message.chat.id, f"✅ Стоимость {merch_type} обновлена до {new_price}!")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Ошибка! Введите корректное число.")



'''
-----------------------

Выдать мерч

-----------------------
'''
@bot.message_handler(func=lambda message: message.text == "Выдать мерч")
def give_merch_to_user(message):
    user = get_admin_by_username('@' + message.from_user.username)
    if user and (user[1] == 0 or user[1] == 1):
        bot.send_message(message.chat.id, "Введите ник пользователя (@username):")
        bot.register_next_step_handler(message, process_fusername)
    else:
        bot.send_message(message.chat.id, "❌ У вас нет доступа к этой команде.")

def process_fusername(m):
    username = m.text.lstrip('@')
    if is_got_merch(username):
        bot.send_message(m.chat.id, f"❌ Пользователь {username} уже получил мерч.")
        return
    if not get_user_by_username(username):
        bot.send_message(m.chat.id, f"❌ Пользователя {username} нет в базе.")
        return

    markup = InlineKeyboardMarkup()

    if check_points(username) >= int(get_merch_price('Раскрасить футболку')) and not got_merch(username, 'pshirt'):
        markup.add(InlineKeyboardButton('Раскрасить футболку', callback_data=f'give_merch:{get_merch_price("Раскрасить футболку")}:pshirt:{username}'))
    if check_points(username) >= get_merch_price('Раскрасить шоппер') and not got_merch(username, 'pshopper'):
        markup.add(InlineKeyboardButton('Раскрасить шоппер', callback_data=f'give_merch:{get_merch_price("Раскрасить шоппер")}:pshopper:{username}'))
    if check_points(username) >= get_merch_price('Футболка') and not got_merch(username, 'shirt'):
        markup.add(InlineKeyboardButton('Футболка', callback_data=f'give_merch:{get_merch_price("Футболка")}:shirt:{username}'))
    if check_points(username) >= get_merch_price('Блокнот') and not got_merch(username, 'notebook'):
        markup.add(InlineKeyboardButton('Блокнот', callback_data=f'give_merch:{get_merch_price("Блокнот")}:notebook:{username}'))
    if check_points(username) >= get_merch_price('ПБ') and not got_merch(username, 'pb'):
        markup.add(InlineKeyboardButton('ПБ', callback_data=f'give_merch:{get_merch_price("ПБ")}:pb:{username}'))


    if markup.keyboard:
        bot.send_message(m.chat.id, f"Выберите мерч пользователю {username}:", reply_markup=markup)
    else:
        bot.send_message(m.chat.id, f"❌ Пользователь {username} не может получить мерч.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("give_merch"))
def process_merch_callback(call):
    _, merch_price, merch_type, username = call.data.split(":")
    s = ''
    if merch_type == 'pshirt':
        s = 'Раскрасить футболку'
    elif merch_type == 'pshopper':
        s = 'Раскрасить шоппер'
    elif merch_type == 'shirt':
        s = 'Футболка'
    elif merch_type == 'notebook':
        s = 'Блокнот'
    elif merch_type == 'pb':
        s = 'ПБ'

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton('Да', callback_data=f'yes:{merch_price}:{merch_type}:{username}'),
        InlineKeyboardButton('Нет', callback_data='no')
    )
    bot.send_message(call.message.chat.id, f"Выдать {username} {s}?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("yes"))
def process_merch_call_yes(call):
    _, merch_price, merch_type, username = call.data.split(":")
    give_merch(username, merch_type)
    update_merch_points(username, merch_price)
    print(int(get_merch_price(merch_type)))
    bot.answer_callback_query(call.id, "✅ Мерч за квест выдан!")
    bot.send_message(call.message.chat.id, f"✅ Пользователю {username} выдан мерч за квест!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("no"))
def process_merch_call_no(call):
    bot.answer_callback_query(call.id, "❌ Операция отменена.")
    bot.send_message(call.message.chat.id, "❌ Операция отменена.")