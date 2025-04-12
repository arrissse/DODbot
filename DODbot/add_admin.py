from bot import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from handlers import stations
from users import get_all_users
from admin import add_admin, get_all_admins, update_admin_questnum, get_admin_by_username, update_admin_info


@bot.message_handler(func=lambda message: message.text == "Добавить админа")
def new_admin(message):
    user = get_admin_by_username('@' + message.from_user.username)
    if user and user[1] == 0:
        bot.send_message(message.chat.id, "Введите ник пользователя (@username):")
        bot.register_next_step_handler(message, process_name)
    else:
        bot.send_message(message.chat.id, "❌ У вас нет доступа к этой команде.")


def process_name(m):
    username = m.text
    users = get_all_users()
    admins = get_all_admins()
    user_list = [user[1] for user in users]
    if username.lstrip('@') not in user_list:
        bot.send_message(
            m.chat.id, f"❌ Пользователь {username} не найден в списке.")
        return
    admin_names = [admin[0].lstrip('@') for admin in admins]
    if username.lstrip('@') in admin_names:
        bot.send_message(
            m.chat.id, f"Пользователь {username} уже является админом.")

    bot.send_message(m.chat.id, "Введите уровень админства (0 - pro-admin, 1 - выдача мерча, 2 - админ фш):")
    bot.register_next_step_handler(m, process_level, username)


def process_level(m, username):
    try:
        admin_level = int(m.text)
    except ValueError:
        bot.send_message(
            m.chat.id, "❌ Уровень админства должен быть целым числом. Попробуйте еще раз.")
        return
    
    if admin_level == 2:
        markup = InlineKeyboardMarkup()
        for name, number in stations.items():
            markup.add(InlineKeyboardButton(name, callback_data=f"select_station_&{username}&{number}&{admin_level}"))

        bot.send_message(m.chat.id, "Выберите номер станции админа:",
                         reply_markup=markup)
    else:
        admin_names = [admin[0].lstrip('@') for admin in get_all_admins()]
        if username.lstrip('@') in admin_names:
            update_admin(m, username, admin_level)
        else:
            add_admin_to_db(m, username, admin_level)

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_station_&"))
def process_number(call):
    _, username, questnum, admin_level = call.data.split("&")
    try:
        admin_names = [admin[0].lstrip('@') for admin in get_all_admins()]
        if username.lstrip('@') in admin_names:
            update_admin(call.message, username, admin_level)
        else:
            add_admin_to_db(call.message, username, admin_level)
        update_admin_questnum(username, questnum)
        bot.send_message(
                call.message.chat.id, f"✅ Админу {username} назначена станция №{questnum}.")
    except Exception as e:
                bot.send_message(
                call.message.chat.id, f"{e}")


def update_admin(m, username, admin_level):
    try:
        update_admin_info(username, admin_level)
        bot.send_message(
            m.chat.id, f"✅ Пользователь {username} теперь является админом с уровнем {admin_level}!")
    except Exception as e:
        bot.send_message(
            m.chat.id, f"❌ Не удалось обновить информацию администратора. {e}")
        print(e)

def add_admin_to_db(m, username, admin_level):
    try:
        admins = get_all_admins()
        admin_usernames = [admin[0] for admin in admins]
        if add_admin(username, admin_level):
            username = username.strip().lstrip('@')
            user_id = None
            for user in get_all_users():
                print(user[1], username)
                if user[1] == username:
                    user_id = user[0]
            if user_id:
                bot.send_message(
                    user_id, "Вас сделали админом. Для получения доступа к админ-меню напишите /start.")
            else:
                bot.send_message(
                    m.chat.id, f"❌ Пользователь {username} не найден среди зарегистрированных пользователей.")
            bot.send_message(
                m.chat.id, f"✅ Пользователь {username} теперь является админом с уровнем {admin_level}!")
        else:
            bot.send_message(
                m.chat.id, f"❌ Не удалось добавить администратора {username}.")

        admins = get_all_admins()
        admin_usernames = [admin[0].lstrip('@') for admin in admins]
        bot.send_message(m.chat.id, f"Список админов: {admin_usernames}")
    except Exception as e:
        bot.send_message(
            m.chat.id, "❌ Не удалось добавить администратора. Возможно, неверный ник.")
        print(e)

