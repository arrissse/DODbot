from bot import bot, router, dp
from aiogram import F
import logging
from datetime import datetime
from aiogram import Bot, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db_manager
from users import get_all_users
from admin import get_admin_by_username
import asyncio

router = Router()
logger = logging.getLogger(__name__)


class NewsletterStates(StatesGroup):
    waiting_text = State()
    waiting_time = State()


async def create_db():
    """Создание таблицы newsletter"""
    try:
        async with db_manager.get_async_connection() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS newsletter (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    send_time TEXT NOT NULL,
                    sent BOOLEAN DEFAULT FALSE
                )
            """)
            logger.info("✅ Таблица newsletter создана/проверена")
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблицы: {str(e)}")
        raise


@router.message(F.text == "Отправить рассылку")
async def handle_newsletter_start(message: Message, state: FSMContext):
    """Обработчик начала создания рассылки"""
    try:
        user = await get_admin_by_username(f"@{message.from_user.username}")
        if user and user.level == 0:
            await message.answer("📝 Введите текст рассылки:")
            await state.set_state(NewsletterStates.waiting_text)
        else:
            await message.answer("❌ Доступ запрещен")
    except Exception as e:
        logger.error(f"Ошибка в handle_newsletter_start: {e}")
        await message.answer("⚠️ Произошла ошибка, попробуйте позже")


@router.message(NewsletterStates.waiting_text)
async def process_newsletter_text(message: Message, state: FSMContext):
    """Обработка текста рассылки"""
    await state.update_data(text=message.text)

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Сейчас", callback_data="send_now")],
        [InlineKeyboardButton(text="⏳ Позже", callback_data="schedule_later")]
    ])

    await message.answer("⏰ Выберите время отправки:", reply_markup=markup)
    await state.set_state(NewsletterStates.waiting_time)


@router.callback_query(NewsletterStates.waiting_time, F.data.in_(["send_now", "schedule_later"]))
async def handle_send_option(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Обработка выбора времени рассылки"""
    try:
        data = await state.get_data()
        text = data['text']

        if callback.data == "send_now":
            await start_immediate_newsletter(bot, text)
            await callback.message.answer("✅ Рассылка начата!")
        else:
            await callback.message.answer("📅 Введите дату и время в формате:\nYYYY-MM-DD HH:MM\n(Например: 2025-03-28 14:30)")
            await state.set_state(NewsletterStates.waiting_time)

        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка в handle_send_option: {e}")
        await callback.answer("❌ Ошибка обработки запроса")


@router.message(NewsletterStates.waiting_time)
async def process_send_time(message: Message, state: FSMContext, bot: Bot):
    """Обработка времени для отложенной рассылки"""
    try:
        data = await state.get_data()
        text = data['text']

        try:
            dt = datetime.strptime(message.text, '%Y-%m-%d %H:%M')
            if dt < datetime.now():
                raise ValueError("Дата в прошлом")

            async with db_manager.get_async_connection() as conn:
                await conn.execute(
                    "INSERT INTO newsletter (message, send_time) VALUES (?, ?)",
                    (text, dt.isoformat())
                )
                await conn.commit()

            await message.answer(f"✅ Запланировано на {message.text}!")

        except ValueError as e:
            error_msg = "❌ Некорректная дата или время" if "unconverted" in str(
                e) else "⏳ Нельзя планировать в прошлое!"
            await message.answer(error_msg)

    except Exception as e:
        logger.error(f"Ошибка в process_send_time: {e}")
    finally:
        await state.clear()


async def start_immediate_newsletter(bot: Bot, text: str):
    """Мгновенная рассылка"""
    try:
        users = await get_all_users()
        total = len(users)
        success = 0

        logger.info(f"Начало рассылки для {total} пользователей")

        for user in users:
            try:
                await bot.send_message(user[0], text)
                success += 1
            except Exception as e:
                logger.warning(f"Ошибка отправки пользователю {user[0]}: {e}")

        logger.info(f"Рассылка завершена. Успешно: {success}/{total}")

    except Exception as e:
        logger.error(f"Критическая ошибка рассылки: {e}")


async def newsletter_scheduler(bot: Bot):
    """Фоновая задача для проверки запланированных рассылок"""
    while True:
        try:
            now = datetime.now().isoformat()

            async with db_manager.get_async_connection() as conn:
                cursor = await conn.execute("""
                    SELECT id, message 
                    FROM newsletter 
                    WHERE send_time <= ? AND sent = FALSE
                """, (now,))

                newsletters = await cursor.fetchall()

                for newsletter_id, message in newsletters:
                    await start_immediate_newsletter(bot, message)
                    await conn.execute("UPDATE newsletter SET sent = TRUE WHERE id = ?", (newsletter_id,))
                    await conn.commit()

        except Exception as e:
            logger.error(f"Ошибка в newsletter_scheduler: {e}")

        await asyncio.sleep(60)
