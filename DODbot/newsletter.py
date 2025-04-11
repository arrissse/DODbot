import sqlite3
import time
from datetime import datetime
from bot import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from users import get_all_users
from admin import get_admin_by_username
import threading
from database import db_lock, db_operation

pending_newsletters = {}


def create_db():
    
        with db_operation() as conn:
            cursor = conn.cursor()

            cursor.execute("""
        CREATE TABLE IF NOT EXISTS newsletter (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            send_time TEXT NOT NULL
        )
    """)

            conn.commit()
            
            print("✅ База данных создана!")


def add_newsletter(message, send_time):
    
        with db_operation() as conn:
            cursor = conn.cursor()

            try:
                dt = datetime.strptime(send_time, '%Y-%m-%d %H:%M')
                formatted_time = dt.strftime('%Y-%m-%d %H:%M')
                cursor.execute(
                    "INSERT INTO newsletter (message, send_time) VALUES (?, ?)", (message, formatted_time))
                conn.commit()
            except ValueError:
                print(
                    f"Ошибка: некорректный формат даты и времени: {send_time}")

            


def send_newsletter():
    while True:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')

        
        with db_operation() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT id, message FROM newsletter WHERE send_time = ?", (current_time,))
                newsletters = cursor.fetchall()

                if newsletters:
                    users = get_all_users()
                    for newsletter in newsletters:
                        for user_id in users:
                            try:
                                bot.send_message(user_id[0], newsletter[1])
                            except Exception as e:
                                print(
                                    f"Ошибка отправки пользователю {user_id[0]}: {e}")

                        cursor.execute(
                            "DELETE FROM newsletter WHERE id = ?", (newsletter[0],))

                conn.commit()
                
        time.sleep(60)


def start_sending_newsletters():
    thread = threading.Thread(target=send_newsletter, daemon=True)
    thread.start()


@bot.message_handler(func=lambda message: message.text == "Отправить рассылку")
def ask_newsletter_text(message):
    user = get_admin_by_username('@' + message.from_user.username)
    if user and user[1] == 0:
        chat_id = message.chat.id
        bot.send_message(chat_id, "📝 Введите текст рассылки:")
        bot.register_next_step_handler(message, ask_send_time)
    else:
        bot.send_message(
            message.chat.id, "❌ У вас нет доступа к этой команде.")


def ask_send_time(message):
    chat_id = message.chat.id
    pending_newsletters[chat_id] = message.text

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🚀 Отправить сейчас",
                             callback_data=f"send_now_{chat_id}"),
        InlineKeyboardButton(
            "⏳ Запланировать", callback_data=f"schedule_later_{chat_id}")
    )

    bot.send_message(chat_id, "Когда отправить рассылку?", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("send_now") or call.data.startswith("schedule_later"))
def handle_send_option(call):
    chat_id = int(call.data.split("_")[-1])
    text = pending_newsletters.get(chat_id, "🔔 Без текста")

    if call.data.startswith("send_now"):
        send_newsletter_now(text)
        bot.send_message(
            chat_id, f"✅ Рассылка отправлена!\n📢 *Текст:* {text}", parse_mode="Markdown")
    else:
        bot.send_message(
            chat_id, "⏳ Введите дату и время в формате: YYYY-MM-DD HH:MM\n(Например: 2025-03-28 14:30)")
        bot.register_next_step_handler(call.message, schedule_newsletter, text)


def schedule_newsletter(message, text):
    chat_id = message.chat.id
    send_time = message.text.strip()

    try:
        datetime.strptime(send_time, '%Y-%m-%d %H:%M')
        add_newsletter(text, send_time)
        bot.send_message(
            chat_id, f"✅ Рассылка запланирована!\n📅 *Дата и время:* {send_time}\n📢 *Текст:* {text}", parse_mode="Markdown")
    except ValueError:
        bot.send_message(
            chat_id, "❌ Неверный формат! Введите дату и время в формате: YYYY-MM-DD HH:MM")


def send_newsletter_now(text):
    users = get_all_users()
    for user in users:
        user_id = user[0]
        try:
            bot.send_message(user_id, text)
            print(f"Рассылка отправлена пользователю {user_id}: {text}")
        except Exception as e:
            print(f"Ошибка при отправке пользователю {user_id}: {e}")


start_sending_newsletters()
