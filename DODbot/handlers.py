from bot import bot
from telebot import types
from users import create_users_table
from admin import create_admins_table
from keyboard import main_keyboard, admin_keyboard, pro_admin_keyboard, mipt_admin_keyboard, quest_keyboard, quest_started_keyboard, continue_quest_keyboard
from users import add_user, start_quest, is_quest_started, check_points, check_st_points
from admin import get_all_admins, add_admin, get_admin_level
from telebot.types import BotCommand

create_admins_table()
create_users_table()

add_admin("@arrisse", 0)
add_admin("@Nikita_Savel", 0)


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
        print(param[-1])
        photo_url = f"img/{param[-1]}.png"
        do_action(m, photo_url)

def do_action(message, photo_url):
    with open(photo_url, "rb") as photo:
        bot.send_photo(message.chat.id, photo, caption="Ваше местоположение: ")

@bot.message_handler(func=lambda message: message.text == "📅 Расписание лекций")
def send_schedule_photo(m):
    photo_url = "img/schedule.png"
    with open(photo_url, "rb") as photo:
        bot.send_photo(m.chat.id, photo,
                   caption="📅 Вот ваше расписание лекций!")

@bot.message_handler(func=lambda message: message.text == "🎯 Квест")
def qwest(message):
    if is_quest_started(message.from_user.username):
        keyboard = quest_started_keyboard()
    else:
        keyboard = quest_keyboard()
        start_quest(message.from_user.username)
    bot.send_message(message.chat.id, "Выберите действие:",
                     reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text == "▶️ Начать")

def start(message):
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

@bot.message_handler(func=lambda message: message.text == "станция ФРКТ")
def quest1(message):
    username = message.from_user.username
    bot.send_message(message.chat.id, "Станция ФРКТ", reply_markup=quest_started_keyboard())
    send_quest_points(message, username, 1)

@bot.message_handler(func=lambda message: message.text == "станция ЛФИ")
def quest2(message):
    bot.send_message(message.chat.id, "Станция ЛФИ", reply_markup=quest_started_keyboard())
    username = message.from_user.username
    send_quest_points(message, username, 2)

@bot.message_handler(func=lambda message: message.text == "станция ФАКТ")
def quest3(message):
    bot.send_message(message.chat.id, "Станция ФАКТ", reply_markup=quest_started_keyboard())
    username = message.from_user.username
    send_quest_points(message, username, 3)

@bot.message_handler(func=lambda message: message.text == "станция ФЭФМ")
def quest4(message):
    bot.send_message(message.chat.id, "Станция ФЭФМ", reply_markup=quest_started_keyboard())
    username = message.from_user.username
    send_quest_points(message, username, 4)

@bot.message_handler(func=lambda message: message.text == "станция ФПМИ")
def quest5(message):
    bot.send_message(message.chat.id, "Станция ФПМИ", reply_markup=quest_started_keyboard())
    username = message.from_user.username
    send_quest_points(message, username, 5)

@bot.message_handler(func=lambda message: message.text == "станция ФБМФ")
def quest6(message):
    bot.send_message(message.chat.id, "Станция ФБМФ", reply_markup=quest_started_keyboard())
    username = message.from_user.username
    send_quest_points(message, username, 6)

@bot.message_handler(func=lambda message: message.text == "станция КНТ")
def quest7(message):
    bot.send_message(message.chat.id, "Станция КНТ", reply_markup=quest_started_keyboard())
    username = message.from_user.username
    send_quest_points(message, username, 7)

@bot.message_handler(func=lambda message: message.text == "станция ФБВТ")
def quest9(message):
    bot.send_message(message.chat.id, "Станция ФБВТ", reply_markup=quest_started_keyboard())
    username = message.from_user.username
    send_quest_points(message, username, 8)

@bot.message_handler(func=lambda message: message.text == "станция ВШПИ")
def quest9(message):
    bot.send_message(message.chat.id, "Станция ВШПИ", reply_markup=quest_started_keyboard())
    username = message.from_user.username
    send_quest_points(message, username, 9)

@bot.message_handler(func=lambda message: message.text == "станция ВШМ")
def quest10(message):
    bot.send_message(message.chat.id, "Станция ВШМ", reply_markup=quest_started_keyboard())
    username = message.from_user.username
    send_quest_points(message, username, 10)

@bot.message_handler(func=lambda message: message.text == "станция ПИШ РПИ")
def quest11(message):
    bot.send_message(message.chat.id, "Станция ПИШ РПИ", reply_markup=quest_started_keyboard())
    username = message.from_user.username
    send_quest_points(message, username, 11)

@bot.message_handler(content_types=["text"])
def handle_text(message):
    responses = {
        "📍 Расположение физтех-школ": "📍 Физтех-школы расположены в кампусе.",
        "🗺 Карта": "🗺 Вот карта университета.",
    }

    response = responses.get(message.text, "❌ Неизвестная команда.")
    bot.send_message(message.chat.id, response)
