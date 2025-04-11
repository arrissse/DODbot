import sqlite3
import time
from datetime import datetime
from bot import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from users import get_all_users
from admin import get_admin_by_username
import threading
import logging
from database import db_manager

pending_newsletters = {}


def create_db():
    """Создание таблицы newsletter с улучшенной структурой"""
    try:
        with db_manager.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS newsletter (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    send_time TEXT NOT NULL,
                    sent BOOLEAN DEFAULT FALSE  # Добавляем статус отправки
                )
            """)
            conn.commit()
            print("✅ Таблица newsletter создана/проверена")
    except Exception as e:
        print(f"❌ Ошибка создания таблицы: {e}")
        raise


def add_newsletter(message, send_time):
    """Добавление рассылки с обработкой ошибок"""
    try:
        dt = datetime.strptime(send_time, '%Y-%m-%d %H:%M')
        formatted_time = dt.isoformat()

        with db_manager.get_connection() as conn:
            conn.execute(
                "INSERT INTO newsletter (message, send_time) VALUES (?, ?)",
                (message, formatted_time))
            conn.commit()

    except ValueError as e:
        bot.send_message(message.chat.id, f"❌ Ошибка формата времени: {e}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка добавления рассылки: {e}")

            
def send_newsletter():
    """Улучшенная логика рассылки с блокировками"""
    while True:
        try:
            current_time = datetime.now().isoformat()

            with db_manager.get_connection() as conn:
                # Выбираем неотправленные рассылки
                cursor = conn.execute("""
                    SELECT id, message 
                    FROM newsletter 
                    WHERE send_time <= ? AND sent = FALSE
                """, (current_time,))

                newsletters = cursor.fetchall()

                if newsletters:
                    users = get_all_users()
                    for newsletter_id, message in newsletters:
                        send_to_users(message, users)

                        # Помечаем как отправленные
                        conn.execute(
                            "UPDATE newsletter SET sent = TRUE WHERE id = ?",
                            (newsletter_id,)
                        )
                        conn.commit()

            time.sleep(60)

        except Exception as e:
            bot.send_message(
                message.chat.id, f"❌ Ошибка в цикле рассылки: {e}")
            time.sleep(10)


def send_to_users(message, users):
    """Отправка сообщений пользователям с обработкой исключений"""
    success = errors = 0
    for user_id, *_ in users:  # Предполагаем структуру (id, ...)
        try:
            bot.send_message(user_id, message)
            success += 1
        except Exception as e:
            bot.send_message(
                message.chat.id, f"❌ Ошибка отправки {user_id}: {str(e)}")
            errors += 1
    bot.send_message(
        message.chat.id, f"✅ Отправлено: {success} | ❌ Ошибок: {errors}")


logger = logging.getLogger(__name__)
pending_newsletters = {}


def start_sending_newsletters():
    """Запуск фонового потока для рассылки с обработкой исключений"""
    try:
        thread = threading.Thread(
            target=send_newsletter,
            name="NewsletterThread",
            daemon=True
        )
        thread.start()
        logger.info("Фоновый поток рассылки запущен")
    except Exception as e:
        logger.error(f"Ошибка запуска потока: {e}")


@bot.message_handler(func=lambda message: message.text == "Отправить рассылку")
def ask_newsletter_text(message):
    """Обработчик команды рассылки с проверкой прав"""
    try:
        username = f"@{message.from_user.username}"
        user = get_admin_by_username(username)

        if user and user.level == 0:  # Предполагаем использование объектов-моделей
            msg = bot.send_message(
                message.chat.id, "📝 Введите текст рассылки:")
            bot.register_next_step_handler(msg, ask_send_time)
        else:
            bot.send_message(message.chat.id, "❌ Доступ запрещен")

    except Exception as e:
        logger.error(f"Ошибка в ask_newsletter_text: {e}")
        bot.send_message(
            message.chat.id, "⚠️ Произошла ошибка, попробуйте позже")


def ask_send_time(message):
    """Сохранение текста рассылки и запрос времени"""
    try:
        chat_id = message.chat.id
        if not message.text:
            raise ValueError("Пустой текст рассылки")

        pending_newsletters[chat_id] = {
            'text': message.text,
            'timestamp': datetime.now()
        }

        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton(
                "🚀 Сейчас", callback_data=f"send_now_{chat_id}"),
            InlineKeyboardButton(
                "⏳ Позже", callback_data=f"schedule_later_{chat_id}")
        )

        bot.send_message(chat_id, "⏰ Выберите время отправки:",
                         reply_markup=markup)

    except Exception as e:
        logger.error(f"Ошибка в ask_send_time: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка обработки запроса")


@bot.callback_query_handler(func=lambda call: call.data.startswith(("send_now", "schedule_later")))
def handle_send_option(call):
    """Обработка выбора времени рассылки"""
    try:
        chat_id = int(call.data.split("_")[-1])
        data = pending_newsletters.get(chat_id)

        if not data:
            raise ValueError("Данные рассылки не найдены")

        if call.data.startswith("send_now"):
            # Запуск в отдельном потоке для избежания блокировки
            threading.Thread(
                target=send_newsletter_now,
                args=(data['text'],)
            ).start()

            bot.send_message(
                chat_id,
                f"✅ Рассылка начата!\nСтек: {len(data['text'])} символов",
                parse_mode="Markdown"
            )
        else:
            msg = bot.send_message(
                chat_id,
                "📅 Введите дату и время в формате:\nYYYY-MM-DD HH:MM\n(Например: 2025-03-28 14:30)"
            )
            bot.register_next_step_handler(
                msg, schedule_newsletter, data['text'])

        # Очистка временных данных
        del pending_newsletters[chat_id]

    except Exception as e:
        logger.error(f"Ошибка в handle_send_option: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка обработки запроса")


def schedule_newsletter(message, text):
    """Планирование рассылки на определенное время"""
    try:
        chat_id = message.chat.id
        send_time = message.text.strip()

        # Валидация даты
        try:
            dt = datetime.strptime(send_time, '%Y-%m-%d %H:%M')
            if dt < datetime.now():
                raise ValueError("Дата в прошлом")

        except ValueError as e:
            error_msg = {
                "Дата в прошлом": "⏳ Нельзя планировать в прошлое время!",
                "unconverted data remains": "⚠️ Неверный формат времени"
            }.get(str(e), "❌ Некорректная дата")

            raise ValueError(error_msg)

        # Добавление в базу данных
        with db_manager.get_connection() as conn:
            conn.execute(
                "INSERT INTO newsletter (message, send_time) VALUES (?, ?)",
                (text, dt.isoformat())
            )
            conn.commit()

        bot.send_message(
            chat_id,
            f"✅ Запланировано на {send_time}!\nСообщение: {text[:50]}...",
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Ошибка в schedule_newsletter: {e}")


def send_newsletter_now(text):
    """Мгновенная рассылка с обработкой исключений"""
    try:
        users = get_all_users()
        total = len(users)
        success = 0

        logger.info(f"Начало рассылки для {total} пользователей")

        for idx, user in enumerate(users, 1):
            try:
                bot.send_message(user.id, text)
                success += 1

                # Логирование прогресса
                if idx % 50 == 0:
                    logger.info(f"Отправлено {idx}/{total} сообщений")

            except Exception as e:
                logger.warning(f"Ошибка отправки пользователю {user.id}: {e}")

        logger.info(f"Рассылка завершена. Успешно: {success}/{total}")

    except Exception as e:
        logger.error(f"Критическая ошибка рассылки: {e}")


try:
    start_sending_newsletters()
except Exception as e:
    logger.critical(f"Не удалось запустить рассылку: {e}")
