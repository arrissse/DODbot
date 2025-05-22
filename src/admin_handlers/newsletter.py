import asyncio
import logging
from datetime import datetime

import aiosqlite
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)

from bot import bot, router
from src.database.admin import get_admin_by_username, get_admin_level
from src.database.base import db_manager
from src.database.users import get_all_users

logger = logging.getLogger(__name__)


class NewsletterStates(StatesGroup):
    """
    Состояния FSM для процесса создания и отправки рассылки.

    Attributes:
        waiting_newsletter_text (State): Ожидание ввода текста рассылки.
        waiting_send_time (State): Ожидание выбора времени отправки (сейчас или позже).
        waiting_custom_time (State): Ожидание пользовательского ввода даты и времени отправки.
    """
    waiting_newsletter_text = State()
    waiting_send_time = State()
    waiting_custom_time = State()


async def init_db():
    """
    Инициализация таблицы newsletter в базе данных, если она ещё не создана.

    Таблица содержит:
        - id: первичный ключ
        - message: текст рассылки
        - send_time: дата и время, когда нужно отправить рассылку

    Raises:
        aiosqlite.Error: При ошибке создания таблицы в базе данных.
    """
    try:
        async with db_manager.get_connection() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS newsletter (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    send_time TEXT NOT NULL
                )
            """)
            logger.info("✅ Таблица newsletter создана/проверена")
    except aiosqlite.Error as err:
        logger.error("❌ Ошибка создания таблицы: %s", str(err))
        raise


async def add_newsletter(newsletter_text: str, send_time: str):
    """
    Добавляет новую рассылку в таблицу newsletter с заданным временем отправки.

    Args:
        newsletter_text (str): Текст сообщения для рассылки.
        send_time (str): Время отправки в формате 'YYYY-MM-DD HH:MM'.
    """
    try:
        date = datetime.strptime(send_time, '%Y-%m-%d %H:%M')
        formatted_time = date.strftime('%Y-%m-%d %H:%M')
        async with db_manager.get_connection() as data_base:
            await data_base.execute(
                "INSERT INTO newsletter (message, send_time) VALUES (?, ?)",
                (newsletter_text, formatted_time)
            )
            await data_base.commit()
            logger.info("✅ Рассылка запланирована на %s", formatted_time)
    except ValueError as err:
        logger.error("Ошибка формата времени: %s", err)


async def newsletter_scheduler(this_bot):
    """
    Планировщик рассылок, запускаемый в фоне.

    Каждую минуту проверяет наличие рассылок, запланированных на текущее время,
    отправляет их всем пользователям и удаляет из базы.

    Args:
        this_bot (Bot): Экземпляр Telegram-бота для отправки сообщений.

    Returns:
        None
    """
    logger.info("✅ Планировщик рассылок активирован")

    while True:
        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
            logger.debug("⌛ Проверка времени: %s", current_time)

            async with db_manager.get_connection() as conn:
                cursor = await conn.execute(
                    "SELECT id, message FROM newsletter WHERE send_time = ?",
                    (current_time,)
                )
                newsletters = await cursor.fetchall()

                if newsletters:
                    users = await get_all_users()
                    logger.info(
                        "📨 Найдено %s рассылок для отправки", len(newsletters))

                    for newsletter in newsletters:
                        newsletter_id, message_text = newsletter
                        success = 0
                        errors = 0

                        if not users:
                            logger.warning("Нет пользователей для рассылки.")
                            return

                        for user in users:
                            try:
                                await this_bot.send_message(
                                    chat_id=int(user['id']),
                                    text=message_text
                                )
                                success += 1
                                await asyncio.sleep(0.1)
                            except Exception as err:
                                logger.error(
                                    "❌ Ошибка отправки %s: %s",
                                    user.get('username', 'N/A'), str(err)
                                )
                                errors += 1

                        await conn.execute(
                            "DELETE FROM newsletter WHERE id = ?",
                            (newsletter_id,)
                        )
                        await conn.commit()
                        logger.info(
                            "✅ Рассылка %s отправлена. Успешно: %s, Ошибок: %s", newsletter_id, success, errors)

            sleep_time = 60 - datetime.now().second
            await asyncio.sleep(sleep_time)

        except Exception as err:
            logger.error(
                "🔥 Критическая ошибка в планировщике: %s", str(err), exc_info=True)
            await asyncio.sleep(60)


@router.message(F.text == "Отправить рассылку")
async def handle_newsletter(message: Message, state: FSMContext):
    """
    Обработчик команды "Отправить рассылку".
    Проверяет уровень доступа пользователя и инициирует FSM для ввода текста рассылки.

    Args:
        message (Message): Входящее сообщение от пользователя.
        state (FSMContext): Контекст состояния FSM.
    """
    user = await get_admin_by_username(f"@{message.from_user.username}")
    level = await get_admin_level(user)
    if user and level == 0:
        await message.answer("📝 Введите текст рассылки:")
        await state.set_state(NewsletterStates.waiting_newsletter_text)
    else:
        await message.answer("❌ Нет доступа!")


@router.message(NewsletterStates.waiting_newsletter_text, F.text)
async def process_newsletter_text(message: Message, state: FSMContext):
    """
    Обрабатывает текст рассылки и предлагает выбрать способ отправки (сейчас или позже).

    Args:
        message (Message): Входящее сообщение с текстом рассылки.
        state (FSMContext): Контекст состояния FSM.
    """
    await state.update_data(text=message.text)

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚀 Сейчас", callback_data="send_now"),
            InlineKeyboardButton(
                text="⏳ Позже", callback_data="schedule_later")
        ]
    ])

    await message.answer("⏰ Выберите время отправки:", reply_markup=markup)
    await state.set_state(NewsletterStates.waiting_send_time)


@router.callback_query(NewsletterStates.waiting_send_time, F.data.in_(["send_now", "schedule_later"]))
async def handle_send_option(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает выбор времени отправки: немедленно или по расписанию.

    Args:
        callback (CallbackQuery): Ответ на нажатие кнопки.
        state (FSMContext): Контекст состояния FSM.
    """
    await callback.answer()
    data = await state.get_data()
    newsletter_text = data.get('text')

    if callback.data == "send_now":
        await send_newsletter(newsletter_text)
        await callback.message.answer("✅ Рассылка начата!")
    else:
        await callback.message.answer("📅 Введите дату и время в формате:\nYYYY-MM-DD HH:MM")
        logger.info("Переход к вводу даты и времени")
        await state.set_state(NewsletterStates.waiting_custom_time)


async def send_newsletter(text: str):
    """
    Немедленно отправляет рассылку всем зарегистрированным пользователям.

    Args:
        text (str): Текст рассылки.

    Raises:
        Exception: В случае критической ошибки при рассылке.
    """
    try:
        users = await get_all_users()
        success = 0
        errors = 0

        for user in users:

            try:
                chat_id = int(user['id'])
                await bot.send_message(chat_id=chat_id, text=text)
                success += 1
            except ValueError:
                logger.error("Некорректный ID пользователя: %s", user['id'])
                errors += 1
                continue
            except Exception as err:
                logger.error(
                    "Ошибка отправки %s: %s", user.get('username', 'N/A'), str(err))
                errors += 1

        logger.info(
            "✅ Рассылка завершена. Успешно: %s | Ошибок: %s", success, errors)
    except Exception as err:
        logger.critical("Критическая ошибка рассылки: %s", str(err))
        raise


@router.message(NewsletterStates.waiting_custom_time, F.text)
async def process_custom_time(message: Message, state: FSMContext):
    """
    Обрабатывает пользовательский ввод даты и времени рассылки.
    Сохраняет рассылку в базу, если формат верный.

    Args:
        message (Message): Входящее сообщение с датой и временем.
        state (FSMContext): Контекст состояния FSM.
    """
    data = await state.get_data()
    newsletter_text = data.get('text')
    send_time = message.text.strip()

    if not newsletter_text:
        await message.answer("❌ Текст рассылки утерян")
        await state.clear()
        return

    try:
        date = datetime.strptime(send_time, '%Y-%m-%d %H:%M')
        formatted_time = date.strftime('%Y-%m-%d %H:%M')

        async with db_manager.get_connection() as conn:
            await conn.execute(
                "INSERT INTO newsletter (message, send_time) VALUES (?, ?)",
                (newsletter_text, formatted_time)
            )
            await conn.commit()

        logger.info("Новая рассылка запланирована на %s", formatted_time)
        await message.answer(f"✅ Рассылка запланирована на {formatted_time}!")
    except ValueError as err:
        logger.error("Ошибка формата времени: %s", err)
        await message.answer("❌ Неверный формат времени! Используйте YYYY-MM-DD HH:MM")
    except Exception as err:
        logger.critical("Ошибка при работе с базой: %s", str(err))
        await message.answer("❌ Ошибка сервера при сохранении рассылки")
    finally:
        await state.clear()
