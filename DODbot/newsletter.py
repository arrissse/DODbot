from bot import bot, router
import asyncio
import logging
from datetime import datetime
from aiogram import F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db_manager
from users import get_all_users
from admin import get_admin_by_username, get_admin_level

logger = logging.getLogger(__name__)

class NewsletterStates(StatesGroup):
    waiting_newsletter_text = State()
    waiting_send_time = State()
    waiting_custom_time = State()


async def init_db():
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
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблицы: {str(e)}")
        raise


async def add_newsletter(newsletter_text: str, send_time: str):
    try:
        dt = datetime.strptime(send_time, '%Y-%m-%d %H:%M')
        formatted_time = dt.strftime('%Y-%m-%d %H:%M')
        async with db_manager.get_connection() as db:
            await db.execute(
                "INSERT INTO newsletter (message, send_time) VALUES (?, ?)",
                (newsletter_text, formatted_time)
            )
            await db.commit()
            logger.info(f"✅ Рассылка запланирована на {formatted_time}")
    except ValueError as e:
        logger.error(f"Ошибка формата времени: {e}")


async def newsletter_scheduler(bot):
    """Проверка и отправка запланированных рассылок каждую минуту."""
    logger.info("✅ Планировщик рассылок активирован")

    while True:
        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
            logger.debug(f"⌛ Проверка времени: {current_time}")

            async with db_manager.get_connection() as conn:
                # Получаем запланированные рассылки по текущему времени
                cursor = await conn.execute(
                    "SELECT id, message FROM newsletter WHERE send_time = ?",
                    (current_time,)
                )
                newsletters = await cursor.fetchall()

                if newsletters:
                    users = await get_all_users()
                    logger.info(
                        f"📨 Найдено {len(newsletters)} рассылок для отправки")

                    for newsletter in newsletters:
                        newsletter_id, message_text = newsletter
                        success = 0
                        errors = 0

                        # Рассылка сообщения всем пользователям
                        for user in users:
                            try:
                                await bot.send_message(
                                    chat_id=int(user['id']),
                                    text=message_text
                                )
                                success += 1
                            except Exception as e:
                                logger.error(
                                    f"❌ Ошибка отправки {user.get('username', 'N/A')}: {str(e)}"
                                )
                                errors += 1

                        # Удаляем рассылку после отправки
                        await conn.execute(
                            "DELETE FROM newsletter WHERE id = ?",
                            (newsletter_id,)
                        )
                        await conn.commit()
                        logger.info(
                            f"✅ Рассылка {newsletter_id} отправлена. Успешно: {success}, Ошибок: {errors}")

            # Ждем до начала следующей минуты
            sleep_time = 60 - datetime.now().second
            logger.debug(f"⏳ Следующая проверка через {sleep_time} сек.")
            await asyncio.sleep(sleep_time)

        except Exception as e:
            logger.error(
                f"🔥 Критическая ошибка в планировщике: {str(e)}", exc_info=True)
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
    """Отправка рассылки сразу всем пользователям."""
    try:
        users = await get_all_users()
        success = 0
        errors = 0

        for user in users:
            try:
                await bot.send_message(chat_id=int(user['id']), text=text)
                success += 1
            except Exception as e:
                logger.error(
                    f"Ошибка отправки {user.get('username', 'N/A')}: {str(e)}")
                errors += 1

        logger.info(
            f"✅ Рассылка завершена. Успешно: {success} | Ошибок: {errors}")
    except Exception as e:
        logger.critical(f"Критическая ошибка рассылки: {str(e)}")
        raise


@router.message(NewsletterStates.waiting_custom_time, F.text)
async def process_custom_time(message: Message, state: FSMContext):
    data = await state.get_data()
    newsletter_text = data.get('text')
    send_time = message.text.strip()

    if not newsletter_text:
        await message.answer("❌ Текст рассылки утерян")
        await state.clear()
        return

    try:
        # Проверка формата времени
        dt = datetime.strptime(send_time, '%Y-%m-%d %H:%M')
        formatted_time = dt.strftime('%Y-%m-%d %H:%M')

        # Запись рассылки в базу
        async with db_manager.get_connection() as conn:
            await conn.execute(
                "INSERT INTO newsletter (message, send_time) VALUES (?, ?)",
                (newsletter_text, formatted_time)
            )
            await conn.commit()

        logger.info(f"Новая рассылка запланирована на {formatted_time}")
        await message.answer(f"✅ Рассылка запланирована на {formatted_time}!")
    except ValueError as e:
        logger.error(f"Ошибка формата времени: {e}")
        await message.answer("❌ Неверный формат времени! Используйте YYYY-MM-DD HH:MM")
    except Exception as e:
        logger.critical(f"Ошибка при работе с базой: {str(e)}")
        await message.answer("❌ Ошибка сервера при сохранении рассылки")
    finally:
        await state.clear()
