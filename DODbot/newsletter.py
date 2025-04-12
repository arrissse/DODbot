from bot import bot, router  # Предполагается, что bot и router уже настроены
from aiogram import F
import logging
from datetime import datetime
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio

from database import db_manager
from users import get_all_users
from admin import get_admin_by_username, get_admin_level

logger = logging.getLogger(__name__)


# Определяем состояния рассылки
class NewsletterStates(StatesGroup):
    waiting_newsletter_text = State()
    waiting_send_time = State()
    waiting_custom_time = State()


async def init_db():
    try:
        async with db_manager.get_connection() as conn:  # Замена get_connection() на get_connection()
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS newsletter (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    send_time TEXT NOT NULL
                )
            """)
            logger.info("✅ Таблица newsletter создана/проверена")
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблицы: {str(e)}")
        raise


async def add_newsletter(newsletter_text: str, send_time: str):
    try:
        dt = datetime.strptime(send_time, '%Y-%m-%d %H:%M')
        formatted_time = dt.strftime('%Y-%m-%d %H:%M')
        async with db_manager.get_connection() as db:  # Замена метода подключения
            await db.execute(
                "INSERT INTO newsletter (message, send_time) VALUES (?, ?)",
                (newsletter_text, formatted_time)
            )
            await db.commit()
            logger.info(f"✅ Рассылка запланирована на {formatted_time}")
    except ValueError as e:
        logger.error(f"Ошибка формата времени: {e}")


async def newsletter_scheduler():
    """Проверка и отправка запланированных рассылок каждую минуту."""
    while True:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        async with db_manager.get_connection() as db:
            async with db.execute(
                "SELECT id, message FROM newsletter WHERE send_time = ?",
                (current_time,)
            ) as cursor:
                newsletters = await cursor.fetchall()

            if newsletters:
                users = await get_all_users()
                for newsletter in newsletters:
                    # newsletter_id - int, message_text - str
                    newsletter_id, message_text = newsletter
                    for user in users:
                        try:
                            # Предполагаем, что у объекта user есть атрибут id и username
                            await bot.send_message(user.id, message_text)
                        except Exception as e:
                            logger.error(
                                f"Ошибка отправки сообщения пользователю {user.username}: {e}")

                    # Удаляем отправленную рассылку
                    async with db_manager.get_connection() as db:
                        await db.execute(
                            "DELETE FROM newsletter WHERE id = ?",
                            (newsletter_id,)
                        )
                        await db.commit()
                        logger.info(
                            f"✅ Рассылка с id {newsletter_id} удалена после отправки")

        await asyncio.sleep(60)


@router.message(F.text == "Отправить рассылку")
async def handle_newsletter(message: Message, state: FSMContext):
    user = await get_admin_by_username(f"@{message.from_user.username}")
    level = await get_admin_level(user)
    if user and level == 0:
        await message.answer("📝 Введите текст рассылки:")
        await state.set_state(NewsletterStates.waiting_newsletter_text)
    else:
        await message.answer("❌ Нет доступа!")


@router.message(NewsletterStates.waiting_newsletter_text, F.text)
async def process_newsletter_text(message: Message, state: FSMContext):
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
    data = await state.get_data()
    newsletter_text = data.get('text')

    if callback.data == "send_now":
        await send_newsletter(newsletter_text)
        await callback.message.answer("✅ Рассылка начата!")
    else:
        await callback.message.answer(
            "📅 Введите дату и время в формате:\nYYYY-MM-DD HH:MM"
        )
        await state.set_state(NewsletterStates.waiting_custom_time)

    await state.clear()


async def send_newsletter(text: str):
    """Отправка рассылки сразу всем пользователям."""
    try:
        users = await get_all_users()
        success = 0
        errors = 0

        for user in users:
            try:
                await bot.send_message(chat_id=user.id, text=text)
                success += 1
            except Exception as e:
                logger.error(f"Ошибка отправки {user.username}: {str(e)}")
                errors += 1

        logger.info(f"✅ Успешно: {success} | ❌ Ошибок: {errors}")
    except Exception as e:
        logger.critical(f"Критическая ошибка рассылки: {str(e)}")
        raise


@router.message(NewsletterStates.waiting_custom_time, F.text)
async def process_custom_time(message: Message, state: FSMContext):
    data = await state.get_data()
    newsletter_text = data.get('text')
    send_time = message.text.strip()

    try:
        await add_newsletter(newsletter_text, send_time)
        await message.answer(f"✅ Рассылка запланирована на {send_time}!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
    finally:
        await state.clear()