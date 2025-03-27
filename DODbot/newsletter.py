import sqlite3
import time
from datetime import datetime
from bot import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from users import get_all_users
import threading

pending_newsletters = {}

def create_db():
    conn = sqlite3.connect("newsletter.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS newsletter (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            send_time TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ База данных создана!")

create_db()

def add_newsletter(message, send_time):
    conn = sqlite3.connect("newsletter.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO newsletter (message, send_time) VALUES (?, ?)", (message, send_time))
    conn.commit()
    conn.close()

def send_newsletter():
    while True:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')  # Получаем текущее время в формате "YYYY-MM-DD HH:MM"
        
        conn = sqlite3.connect("newsletter.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, message FROM newsletter WHERE send_time = ?", (current_time,))
        newsletters = cursor.fetchall()
        
        if newsletters:
            for newsletter in newsletters:
                users = get_all_users()

                for user_id in users:
                    bot.send_message(user_id[0], newsletter[1])
                cursor.execute("DELETE FROM newsletter WHERE id = ?", (newsletter[0],))
        
        conn.commit()
        conn.close()

        time.sleep(60)

def start_sending_newsletters():
    threading.Thread(target=send_newsletter, daemon=True).start()


@bot.message_handler(func=lambda message: message.text == "📢 Отправить рассылку")
def ask_newsletter_text(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "📝 Введите текст рассылки:")
    bot.register_next_step_handler(message, ask_send_time)

def ask_send_time(message):
    chat_id = message.chat.id
    pending_newsletters[chat_id] = message.text

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🚀 Отправить сейчас", callback_data="send_now"),
        InlineKeyboardButton("⏳ Запланировать", callback_data="schedule_later")
    )

    bot.send_message(chat_id, "Когда отправить рассылку?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["send_now", "schedule_later"])
def handle_send_option(call):
    chat_id = call.message.chat.id
    text = call.message.text

    if call.data == "send_now":
        send_newsletter_now(text)
        bot.send_message(chat_id, f"✅ Рассылка отправлена!\n📢 *Текст:* {text}", parse_mode="Markdown")
    else:
        bot.send_message(chat_id, "⏳ Введите дату и время в формате: YYYY-MM-DD HH:MM\n(Например: 2025-03-28 14:30)")
        bot.register_next_step_handler(call.message, text, schedule_newsletter)

def schedule_newsletter(message, text):
    chat_id = message.chat.id
    send_time = message.text
  
    bot.send_message(chat_id, f"✅ Рассылка запланирована!\n📅 *Дата и время:* {send_time}\n📢 *Текст:* {text}", parse_mode="Markdown")

    add_newsletter(text, send_time)

def send_newsletter_now(text):
    users = get_all_users()
    for user in users:
        user_id = user[0]
        try:
            bot.send_message(user_id, text)
            print(f"Рассылка отправлена пользователю {user_id}: {text}")
        except Exception as e:
            print(f"Ошибка при отправке рассылки пользователю {user_id}: {e}")
