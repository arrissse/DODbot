from bot import bot
from telebot import types
from users import create_users_table
from admin import create_admins_table
from keyboard import main_keyboard, admin_keyboard, pro_admin_keyboard, mipt_admin_keyboard, quest_keyboard, quest_started_keyboard, continue_quest_keyboard
from users import add_user, start_quest, is_quest_started, check_points, check_st_points
from admin import get_all_admins, add_admin, get_admin_level
from telebot.types import BotCommand
from merch import create_merch_table
from quiz import create_quiz_table

create_quiz_table()
create_merch_table()
create_admins_table()
create_users_table()

add_admin("@arrisse", 0)
add_admin("@Nikita_Savel", 0)

'''
-----------------------

Старт + обработка QR-кодов

-----------------------
'''


@bot.message_handler(commands=["start"])
def start(m):
    add_user(m.chat.id, m.from_user.username)
    current_username = '@' + m.from_user.username
    admins = get_all_admins()
    admin_usernames = [admin[0] for admin in admins]
    print(admin_usernames)
    keyboard = main_keyboard()

    print(f"Список админов: {admin_usernames}")
    print(f"Пользователь: {current_username}")

    bot.set_my_commands([BotCommand("start", "Перезапустить бота")])

    if current_username in admin_usernames:
        admin_level = get_admin_level(current_username)
        print(f"Уровень админства для {current_username}: {admin_level}")
        if admin_level == 0:
            keyboard = pro_admin_keyboard()
        elif admin_level == 1:
            keyboard = admin_keyboard()
        elif admin_level == 2:
            keyboard = mipt_admin_keyboard()
        bot.send_message(m.chat.id, "🔑 Админ-меню:", reply_markup=keyboard)
    else:
        add_user(m.chat.id, m.from_user.username)
        bot.send_message(m.chat.id, "📌 Выберите действие:",
                         reply_markup=keyboard)
    parts = m.text.split()
    if len(parts) > 1:
        param = parts[1]
    
        try:
            if int(param[-2:]) >= 10:
                name = param[-2:]
            else:
                name = param[-1]
        except ValueError:
            name = param[-1]
    
    photo_url = f"img/{name}.png"
    do_action(m, photo_url)

def do_action(message, photo_url):
    with open(photo_url, "rb") as photo:
        bot.send_photo(message.chat.id, photo, caption="Ваше местоположение: ")

'''
-----------------------

Расписание лекций

-----------------------
'''

@bot.message_handler(func=lambda message: message.text == "📅 Расписание лекций")
def send_schedule_photo(m):
    photo_url = "img/schedule.png"
    try:
        with open(photo_url, "rb") as photo:
            bot.send_photo(m.chat.id, photo, caption="📅 Расписание лекций:")
    except Exception as e:
        bot.send_message(m.chat.id, f"Ошибка при отправке: {e}")

'''
-----------------------

Квест

-----------------------
'''

@bot.message_handler(func=lambda message: message.text == "🎯 Квест")
def qwest(message):
    if is_quest_started(message.from_user.username):
        keyboard = quest_started_keyboard()
    else:
        keyboard = quest_keyboard()
    bot.send_message(message.chat.id, "Выберите действие:",
                     reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text == "▶️ Начать")

def start(message):
    start_quest(message.from_user.username)
    markup = continue_quest_keyboard()
    bot.send_message(message.chat.id, "Выберите станцию:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "▶️ Продолжить")
def continue_quest(message):
    markup = continue_quest_keyboard()
    bot.send_message(message.chat.id, "Выберите станцию:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "⬅️ Назад")
def back(message):
    bot.send_message(message.chat.id, "Вы снова в главном меню",
                     reply_markup=main_keyboard())


def send_quest_points(message, username, station):
    bot.send_message(message.chat.id, f"Всего баллов: {check_points(username)}", reply_markup=quest_started_keyboard())
    bot.send_message(message.chat.id, f"Баллы за данную станцию: {check_st_points(username, station)}", reply_markup=quest_started_keyboard())

stations = {
    "станция ФРКТ": 1,
    "станция ЛФИ": 2,
    "станция ФАКТ": 3,
    "станция ФЭФМ": 4,
    "станция ФПМИ": 5,
    "станция ФБМФ": 6,
    "станция КНТ": 7,
    "станция ФБВТ": 8,
    "станция ВШПИ": 9,
    "станция ВШМ": 10,
    "станция ПИШ РПИ": 11
}

@bot.message_handler(func=lambda message: message.text in stations)
def handle_station(message):
    station_number = stations[message.text]
    bot.send_message(message.chat.id, message.text, reply_markup=quest_started_keyboard())
    send_quest_points(message, message.from_user.username, station_number)

'''
-----------------------

Карта

-----------------------
'''

@bot.message_handler(func=lambda message: message.text == "🗺 Карта")
def send_map_photo(message):
    photo_url = "img/schedule.png"
    try:
        with open(photo_url, "rb") as photo:
            bot.send_photo(message.chat.id, photo, caption="🗺 Карта института:")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при отправке: {e}")
