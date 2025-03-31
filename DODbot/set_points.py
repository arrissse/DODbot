from bot import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboard import main_keyboard
from users import update_user_points, get_user_by_username, is_quest_started
from users import update_user_queststation
from admin import get_admin_by_username, get_admin_level
from handlers import stations

@bot.message_handler(func=lambda message: message.text == "Квест. Проставить баллы")
def set_points(message):
    user = get_admin_by_username('@' + message.from_user.username)
    level = get_admin_level('@' + message.from_user.username)
    if user and (level == 0 or level == 2):
        bot.send_message(message.chat.id, "Введите ник пользователя (@username):")
        bot.register_next_step_handler(message, process_username)
    else:
        bot.send_message(message.chat.id, "❌ У вас нет доступа к этой команде.")


def process_username(m):
    username = m.text.strip().lstrip('@')

    admin = get_admin_by_username('@' + m.from_user.username)
    admin_num = admin[2]

    user = get_user_by_username(username)

    if user is None:
        bot.send_message(m.chat.id, f"❌ Пользователь {username} не найден!")
        return

    if admin[1] == 0:
        markup = InlineKeyboardMarkup()
        for i in stations:
            markup.add(InlineKeyboardButton(
                f"{stations[i]}", callback_data=f"select_station&{username}&{i}"))

        bot.send_message(m.chat.id, "Выберите номер станции:",
                         reply_markup=markup)
    elif admin[1] == 2:
        if user[admin_num + 2] != 0:
            bot.send_message(
                m.chat.id, f"❌ Пользователю {username} уже начислены баллы.")
            return
        process_points_selection(m.chat.id, username, admin[2], user)
    else:
        bot.send_message(
            m.chat.id, "❌ У вас нет доступа ставить баллы.", reply_markup=main_keyboard())


@bot.callback_query_handler(func=lambda call: call.data.startswith("select_station&"))
def process_station_selection(call):
    bot.answer_callback_query(call.id)

    _, username, admin_num = call.data.split("&")
    admin_num = int(admin_num)

    user = get_user_by_username(username)
    if user is None:
        bot.send_message(call.message.chat.id,
                         f"❌ Пользователь {username} не найден!")
        return

    if user[admin_num + 2] != 0:
        bot.send_message(call.message.chat.id,
                         f"❌ Пользователю {username} уже начислены баллы.")
        return

    bot.send_message(call.message.chat.id, f"✅ Вы выбрали станцию {admin_num}")

    process_points_selection(call.message.chat.id, username, admin_num, user)


def process_points_selection(chat_id, username, admin_num, user):
    if not is_quest_started(username):
        bot.send_message(
            chat_id, f"❌ Пользователь {username} ещё не начал принимать участие в квесте.")
        return
    if user[admin_num + 2] != 0:
        bot.send_message(
            chat_id, f"❌ Пользователю {username} уже начислены баллы.")
        return

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(
            "1️⃣", callback_data=f"points&{username}&{admin_num}&1"),
        InlineKeyboardButton(
            "2️⃣", callback_data=f"points&{username}&{admin_num}&2")
    )
    markup.add(
        InlineKeyboardButton("🔙 Назад", callback_data=f"back_to_stations&{username}")
    )

    bot.send_message(
        chat_id, f"Выберите количество баллов для пользователя {username}:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("back_to_stations&"))
def back_to_stations(call):
    bot.answer_callback_query(call.id)

    _, username = call.data.split("&")
    
    bot.send_message(call.message.chat.id, f"🔙 Возвращаемся к выбору станции для {username}.")
    
    markup = InlineKeyboardMarkup()
    for i in range(1, 12):
        markup.add(InlineKeyboardButton(
            f"Станция {i}", callback_data=f"select_station&{username}&{i}"))

    bot.send_message(call.message.chat.id, "Выберите номер станции:",
                         reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("points&"))
def process_points_callback(call):
    bot.answer_callback_query(call.id, f"✅ Баллы начислены!")

    _, username, admin_num, points = call.data.split("&")
    admin_num = int(admin_num)
    points = int(points)

    user = get_user_by_username(username)
    if user is None:
        bot.send_message(call.message.chat.id,
                         f"❌ Пользователь {username} не найден!")
        return

    update_user_points(username, admin_num, points)
    update_user_queststation(username)
    bot.send_message(call.message.chat.id,
                     f"✅ Пользователю {username} начислено {points} баллов!")