import logging
from datetime import datetime
from urllib.parse import unquote

from aiogram import F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (CallbackQuery, FSInputFile, InlineKeyboardButton,
                           Message)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot import router
from constants import DEFAULT_MERCH_PRICES, QUIZ_LIST
from src.database.admin import (get_admin_by_username, get_admin_level,
                                save_admins_to_excel)
from src.database.base import db_manager
from src.database.merch import (add_column, give_merch, got_merch,
                                is_got_merch, save_merch_to_excel)
from src.database.users import (check_points, count_active_quests,
                                count_finished_quests, get_user_by_username,
                                save_users_to_excel, update_merch_points)
from src.keyboard import (main_keyboard, pro_admin_keyboard, pro_admin_merch,
                          pro_admin_quiz_start)
from src.user_handlers.quiz import update_quiz_time


class Form(StatesGroup):
    """
    FSM states для работы с выдачей и редактированием мерча.
    """
    waiting_username = State()
    waiting_merch_type = State()
    waiting_new_price = State()
    waiting_merch_name = State()
    waiting_merch_cost = State()
    waiting_delete_merch = State()
    edit_price = State()


# -----------------------------------------------------------------------------
# /admins
# -----------------------------------------------------------------------------
@router.message(Command("admins"))
async def send_admins_list(message: Message):
    """
    Отправляет файл со списком администраторов в Excel.

    При уровне админа 0 генерирует и шлёт файл, иначе сообщает об отказе.

    Args:
        message (Message): Входящее сообщение с командой /admins.
    """
    username = f'@{message.from_user.username}'
    user = await get_admin_by_username(username)
    level = await get_admin_level(username) if user else None

    if user and level == 0:
        filename = await save_admins_to_excel()
        print(f"Файл Excel создан: {filename}")

        if filename:
            await message.answer_document(FSInputFile(filename))
        else:
            await message.answer("❌ В базе данных нет пользователей.")
    else:
        await message.answer("❌ У вас нет доступа к этой команде.")


# -----------------------------------------------------------------------------
# /merch
# -----------------------------------------------------------------------------
@router.message(Command("merch"))
async def send_merch_list(message: Message):
    """
    Отправляет файл с текущим списком мерча в Excel.

    Только для админа уровня 0. Если база пуста — пишет об этом.

    Args:
        message (Message): Входящее сообщение с командой /merch.
    """
    username = f'@{message.from_user.username}'
    user = await get_admin_by_username(username)
    level = await get_admin_level(username) if user else None

    if user and level == 0:
        filename = await save_merch_to_excel()
        print(f"Файл Excel создан: {filename}")

        if filename:
            await message.answer_document(FSInputFile(filename))
        else:
            await message.answer("❌ База данных пуста.")
    else:
        await message.answer("❌ У вас нет доступа к этой команде.")


# -----------------------------------------------------------------------------
# Мерч (для админа 0 уровня)
# -----------------------------------------------------------------------------
@router.message(F.text == "Мерч")
async def pro_admin_merch_button(message: Message):
    """
    Показывает подменю мерча для администратора уровня 0.

    Args:
        message (Message): Входящее сообщение с текстом «Мерч».
    """
    username = f'@{message.from_user.username}'
    user = await get_admin_by_username(username)
    level = await get_admin_level(username) if user else None

    try:
        if user and level == 0:
            await message.answer("Выберите действие:", reply_markup=pro_admin_merch())
        else:
            await message.answer("❌ У вас нет доступа к этой команде.")
    except Exception as err:
        await message.answer(str(err))


@router.message(F.text == "Назад ⬅️")
async def pro_admin_merch_back(message: Message):
    """
    Возвращает администратора из меню мерча в главное админ-меню.

    Args:
        message (Message): Входящее сообщение с текстом «Назад ⬅️».
    """
    username = f'@{message.from_user.username}'
    user = await get_admin_by_username(username)
    level = await get_admin_level(username) if user else None
    try:
        if user and level == 0:
            await message.answer("🔑 Админ-меню:", reply_markup=pro_admin_keyboard())
        else:
            await message.answer("❌ У вас нет доступа к этой команде.")
    except Exception as err:
        await message.answer(str(err))


# -----------------------------------------------------------------------------
# Начать квиз (для админа 0 уровня)
# -----------------------------------------------------------------------------
@router.message(F.text == "Начать квиз")
async def pro_admin_quiz_button(message: Message):
    """
    Открывает подменю выбора квиза для администратора уровня 0.

    Args:
        message (Message): Входящее сообщение с текстом «Начать квиз».
    """
    username = f'@{message.from_user.username}'
    user = await get_admin_by_username(username)
    level = await get_admin_level(username) if user else None
    try:
        if user and level == 0:
            await message.answer("Выберите квиз:", reply_markup=pro_admin_quiz_start())
        else:
            await message.answer("❌ У вас нет доступа к этой команде.")
    except Exception as err:
        await message.answer(str(err))


@router.message(F.text.in_(QUIZ_LIST))
async def handle_quiz_start(message: Message):
    """
    Спрашивает у пользователя, действительно ли он хочет начать выбранный квиз.

    Args:
        message (Message): Входящее сообщение с текстом «Квиз N».
    """
    quiz_number = QUIZ_LIST[message.text]
    markup = InlineKeyboardBuilder()
    markup.button(text="Да", callback_data=f"start_quiz:{quiz_number}")
    markup.button(text="Нет", callback_data="not_start_quiz")
    await message.answer(f"Начать {message.text}?", reply_markup=markup.as_markup())


@router.callback_query(F.data.startswith("start_quiz:"))
async def start_quiz(call: CallbackQuery):
    """
    Запускает квиз: проверяет наличие в БД и обновляет время старта.

    Args:
        call (CallbackQuery): Колбэк от нажатия «Да» в вопросе «Начать квиз?».

    Returns:
        None
    """
    try:
        await call.answer()
        _, quiz_id = call.data.split(":")
        quiz_id = int(quiz_id)
        async with db_manager.get_connection() as conn:
            cur = await conn.execute(
                "SELECT * FROM quiz_schedule WHERE id = ?",
                (quiz_id,)
            )
            quiz_info = await cur.fetchone()
        if not quiz_info:
            return await call.message.answer("Ошибка: квиз не найден.")
        quiz_name = quiz_info[0]
        current_time = datetime.now().strftime("%H:%M")
        await update_quiz_time(quiz_id, current_time)
        await call.message.answer(f"✅ {quiz_name} начат!")
    except Exception as err:
        await call.message.answer(f"❌ {str(err)}")


@router.callback_query(F.data.startswith("not_start_quiz"))
async def cancel_quiz(call: CallbackQuery):
    """
    Обрабатывает отказ от запуска квиза.

    Args:
        call (CallbackQuery): Колбэк с данными «not_start_quiz».
    """
    await call.answer("❌ Операция отменена.")
    await call.message.answer("❌ Операция отменена.")


# -----------------------------------------------------------------------------
# Таблица пользователей
# -----------------------------------------------------------------------------
@router.message(F.text == "Таблица пользователей")
async def send_users_list(message: Message):
    """
    Генерирует и отправляет файл Excel со всеми пользователями (по правам админа).

    Args:
        message (Message): Входящее сообщение с текстом «Таблица пользователей».
    """
    user = await get_admin_by_username(f'@{message.from_user.username}')
    if user:
        filename = await save_users_to_excel()
        if filename:
            await message.answer_document(FSInputFile(filename))
        else:
            await message.answer("❌ В базе данных нет пользователей.")
    else:
        await message.answer("❌ У вас нет доступа к этой команде.")


# -----------------------------------------------------------------------------
# Переключить меню
# -----------------------------------------------------------------------------
@router.message(F.text == "Переключить меню")
async def chage_menu(message: Message):
    """
    Подсказка по повторному переключению меню после его смены.

    Args:
        message (Message): Входящее сообщение с текстом «Переключить меню».
    """
    await message.answer("Для повторного переключения меню введите /start", reply_markup=main_keyboard())


# -----------------------------------------------------------------------------
# Квест. Текущая статистика
# -----------------------------------------------------------------------------
@router.message(F.text == "Квест. Текущая статистика")
async def statistics(message: Message):
    """
    Показывает число пользователей, начавших и завершивших квест.

    Args:
        message (Message): Входящее сообщение с текстом «Квест. Текущая статистика».
    """
    user = await get_admin_by_username(f'@{message.from_user.username}')
    if user:
        active_users = await count_active_quests()
        finished_users = await count_finished_quests()
        await message.answer(f"Количество пользователей, начавших квест: {active_users}\n"
                             f"Количество пользователей, завершивших квест: {finished_users}\n")
    else:
        await message.answer("❌ У вас нет доступа к этой команде.")


# -----------------------------------------------------------------------------
# Стоимость мерча (для админа 0 уровня)
# -----------------------------------------------------------------------------
async def create_price_table():
    """
    Создаёт в БД таблицу merch_prices и инициализирует её предопределёнными значениями.
    """
    async with db_manager.get_connection() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS merch_prices (
                merch_type TEXT PRIMARY KEY,
                price INTEGER DEFAULT 0
            )
        """)
        await conn.executemany(
            "INSERT OR IGNORE INTO merch_prices (merch_type, price) VALUES (?, ?)",
            DEFAULT_MERCH_PRICES
        )
        await conn.commit()


async def get_merch_types():
    """
    Возвращает список всех доступных типов мерча из таблицы merch_prices.

    Returns:
        List[str]: Список названий мерч-типов.
    """
    async with db_manager.get_connection() as conn:
        cursor = await conn.execute("SELECT merch_type FROM merch_prices")
        result = await cursor.fetchall()
        return [row['merch_type'] for row in result]


async def get_merch_price(merch_type: str):
    """
    Получает цену заданного типа мерча.

    Args:
        merch_type (str): Название типа мерча.

    Returns:
        Optional[int]: Цена или None, если тип не найден.
    """
    async with db_manager.get_connection() as conn:
        async with conn.execute(
            "SELECT price FROM merch_prices WHERE merch_type = ?",
            (merch_type,)
        ) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None


async def update_merch_price(merch_type, new_price):
    """
    Обновляет или вставляет запись о цене мерча в таблицу merch_prices.

    Args:
        merch_type (str): Название типа мерча.
        new_price (int): Новая цена.
    """
    async with db_manager.get_connection() as conn:
        await conn.execute("""
            INSERT INTO merch_prices (merch_type, price)
            VALUES (?, ?)
            ON CONFLICT (merch_type) DO UPDATE SET price = ?
        """, (merch_type, new_price, new_price))
        await conn.commit()


@router.message(F.text == "Стоимость мерча")
async def merch_prices_menu(message: Message):
    """
    Предлагает администратору выбрать товар для изменения стоимости.

    Args:
        message (Message): Входящее сообщение с текстом «Стоимость мерча».
    """
    async with db_manager.get_connection() as conn:
        cursor = await conn.execute("SELECT merch_type FROM merch_prices")
        result = await cursor.fetchall()
        merch_types = [row[0] for row in result]

        markup = InlineKeyboardBuilder()
        for merch in merch_types:
            markup.row(InlineKeyboardButton(
                text=merch,
                callback_data=f"edit_price:{merch}"
            ))

        await message.answer(
            "Выберите товар для изменения стоимости:",
            reply_markup=markup.as_markup()
        )


@router.callback_query(F.data.startswith("edit_price"))
async def edit_price_handler(call: CallbackQuery, state: FSMContext):
    """
    Начинает FSM-диалог редактирования цены мерча: сохраняет тип и переходит в состояние Form.edit_price.

    Args:
        call (CallbackQuery): Колбэк от нажатия товара в меню «Стоимость мерча».
        state (FSMContext): Текущий FSM-контекст.
    """
    await call.answer()
    merch_type = call.data.split(":")[1]
    await state.update_data(merch_type=merch_type)
    await state.set_state(Form.edit_price)
    current_price = await get_merch_price(merch_type)
    await call.message.answer(f"Текущая стоимость {merch_type}: {current_price}\nВведите новую стоимость:")


@router.message(Form.edit_price)
async def process_new_price(message: Message, state: FSMContext):
    """
    Обрабатывает ввод новой цены: если корректное число — обновляет в БД, иначе просит повторить.

    Args:
        message (Message): Входящее сообщение с введённым значением.
        state (FSMContext): Текущий FSM-контекст.
    """
    data = await state.get_data()
    merch_type = data['merch_type']
    try:
        new_price = int(message.text)
        await update_merch_price(merch_type, new_price)
        await message.answer(f"✅ Стоимость {merch_type} обновлена до {new_price}!")
    except ValueError:
        await message.answer("❌ Ошибка! Введите корректное число.")
    await state.clear()


# -----------------------------------------------------------------------------
# Выдать мерч (для админов 0 и 1 уровней)
# -----------------------------------------------------------------------------
@router.message(F.text == "Выдать мерч")
async def give_merch_to_user(message: Message, state: FSMContext):
    """
    Начинает выдачу мерча — переводит FSM в состояние ожидания ника пользователя.

    Args:
        message (Message): Входящее сообщение с текстом «Выдать мерч».
        state (FSMContext): Текущий FSM-контекст.
    """
    user = await get_admin_by_username(f'@{message.from_user.username}')
    if user and (user[1] == 0 or user[1] == 1):
        await message.answer("Введите ник пользователя (@username):")
        await state.set_state(Form.waiting_username)
    else:
        await message.answer("❌ У вас нет доступа к этой команде.")


@router.message(Form.waiting_username)
async def process_fusername(message: Message, state: FSMContext):
    """
    Проверяет введённый ник, формирует меню выбора конкретного мерча
    на InlineKeyboard по оставшимся баллам и сразу очищает FSM.

    Args:
        message (Message): Входящее сообщение с ником пользователя.
        state (FSMContext): Текущий FSM-контекст.
    """
    try:
        if message.text[0] != '@':
            await message.answer("❌ Введите корректно ник пользователя.")
            return

        username = message.text.lstrip('@')
        if await is_got_merch(username):
            await message.answer(f"❌ Пользователь {username} уже получил мерч.")
            return

        if not await get_user_by_username(username):
            await message.answer(f"❌ Пользователя {username} нет в базе.")
            return

        await state.update_data(username=username)
        markup = InlineKeyboardBuilder()
        merch_types = await get_merch_types()

        for merch in merch_types:
            price = await get_merch_price(merch)

            if (
                await check_points(username.strip('@')) >= price
                and not await got_merch(username, merch)
            ):
                callback_data = f"give_merch:{str(price)}:{str(merch)}:{str(username)}"
                markup.add(InlineKeyboardButton(
                    text=f"{merch}: {price}",
                    callback_data=callback_data
                ))
        logging.info("murkup_added")
        markup = markup.as_markup()
        if markup.inline_keyboard:
            await message.answer(
                f"Количество баллов {username}: {await check_points(username)}. "
                f"Выберите мерч:",
                reply_markup=markup
            )
        else:
            await message.answer(f"❌ Недостаточно баллов: {await check_points(username.strip('@'))}")

        await state.clear()

    except Exception as err:
        await message.answer(f"❌ Ошибка: {str(err)}")
        await state.clear()


@router.callback_query(F.data.startswith("give_merch"))
async def process_merch_callback(call: CallbackQuery):
    """
    Спрашивает подтверждение выдачи выбранного мерча пользователю.

    Args:
        call (CallbackQuery): Колбэк с данными о цене, типе мерча и нике пользователя.
    """
    _, merch_price, merch_type, username = call.data.split(":")

    markup = InlineKeyboardBuilder()

    markup.row(
        InlineKeyboardButton(
            text='Да',
            callback_data=f'yes:{merch_price}:{merch_type}:{username}'
        ),
        InlineKeyboardButton(
            text='Нет',
            callback_data='no'
        )
    )

    await call.message.answer(
        f"Выдать {username} {merch_type}?",
        reply_markup=markup.as_markup()
    )


@router.callback_query(F.data.startswith("yes"))
async def process_merch_call_yes(call: CallbackQuery):
    """
    Обрабатывает подтверждение выдачи мерча: списывает баллы и шлёт уведомления.

    Args:
        call (CallbackQuery): Колбэк с данными цены, типа мерча и ника пользователя.
    """
    data_parts = call.data.split(":")
    _, merch_price_enc, merch_type_enc, username_enc = data_parts
    merch_price = unquote(merch_price_enc)
    merch_type = unquote(merch_type_enc)
    username = unquote(username_enc)
    logging.info("%s, %s", merch_type, username)
    await give_merch(username, merch_type)
    await update_merch_points(username, merch_price)
    await call.answer("✅ Мерч за квест выдан!")
    await call.message.answer(f"✅ Пользователю {username} выдан мерч за квест!")


@router.callback_query(F.data.startswith("no"))
async def process_merch_call_no(call: CallbackQuery):
    """
    Отменяет выдачу мерча по нажатию «Нет».

    Args:
        call (CallbackQuery): Колбэк с данными «no».
    """
    await call.answer("❌ Операция отменена.")
    await call.message.answer("❌ Операция отменена.")


# -----------------------------------------------------------------------------
# Добавить позицию мерча (для админа 0 уровня)
# -----------------------------------------------------------------------------
@router.message(F.text == "Добавить позицию мерча")
async def add_merch_type(message: Message, state: FSMContext):
    """
    Переводит FSM в состояние ожидания названия новой позиции мерча.

    Args:
        message (Message): Входящее сообщение с текстом «Добавить позицию мерча».
        state (FSMContext): Текущий FSM-контекст.
    """
    user = await get_admin_by_username(f'@{message.from_user.username}')
    if user and user[1] == 0:
        await message.answer("Введите название новой позиции мерча:")
        await state.set_state(Form.waiting_merch_name)
    else:
        await message.answer("❌ У вас нет доступа к этой команде.")


@router.message(Form.waiting_merch_name)
async def process_type(message: Message, state: FSMContext):
    """
    Сохраняет название новой позиции в FSM и запрашивает её стоимость.

    Args:
        message (Message): Входящее сообщение с названием мерча.
        state (FSMContext): Текущий FSM-контекст.
    """
    await state.update_data(type=message.text)
    await message.answer("Введите стоимость новой позиции мерча:")
    await state.set_state(Form.waiting_merch_cost)


@router.message(Form.waiting_merch_cost)
async def process_type_cost(message: Message, state: FSMContext):
    """
    Пытается преобразовать введённую стоимость в целое число и добавить новую колонку в таблицу merch.

    Args:
        message (Message): Входящее сообщение с введённой стоимостью.
        state (FSMContext): Текущий FSM-контекст.
    """
    try:
        data = await state.get_data()
        merch_type = data['type']
        cost = int(message.text)
    except ValueError:
        await message.answer("❌ Стоимость должна быть числом. Попробуйте ещё раз.")
        await state.clear()
        return
    async with db_manager.get_connection() as conn:
        await conn.execute("""
            INSERT OR IGNORE INTO merch_prices (merch_type, price) VALUES (?, ?)
        """, (merch_type, cost))
    try:
        await add_column(merch_type)
    except Exception as err:
        await message.answer(f"❌ Ошибка при добавлении колонки: {err}")
        await state.clear()
        return
    await message.answer(f"✅ Позиция '{merch_type}' добавлена с ценой {cost} баллов.")
    await state.clear()


# -----------------------------------------------------------------------------
# Удалить позицию мерча (для админа 0 уровня)
# -----------------------------------------------------------------------------
@router.message(F.text == "Удалить позицию мерча")
async def remove_merch_type(message: Message, state: FSMContext):
    """
    Переводит FSM в состояние ожидания названия позиции мерча для удаления.

    Args:
        message (Message): Входящее сообщение с текстом «Удалить позицию мерча».
        state (FSMContext): Текущий FSM-контекст.
    """
    user = await get_admin_by_username(f'@{message.from_user.username}')
    if user and user[1] == 0:
        await message.answer("Введите название позиции мерча, которую необходимо удалить:")
        await state.set_state(Form.waiting_delete_merch)
    else:
        await message.answer("❌ У вас нет доступа к этой команде.")


@router.message(Form.waiting_delete_merch)
async def process_r_type(message: Message, state: FSMContext):
    """
    Удаляет из БД позицию мерча, если она есть, и очищает FSM.

    Args:
        message (Message): Входящее сообщение с названием позиции мерча.
        state (FSMContext): Текущий FSM-контекст.
    """
    merch_type = message.text.strip()
    try:
        async with db_manager.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM merch_prices WHERE merch_type = ?",
                (merch_type,)
            )
            result = await cursor.fetchone()
            count = result[0] if result else 0
            if count == 0:
                await message.answer(f"❌ Позиция '{merch_type}' не найдена.")
                await state.clear()
                return
            await conn.execute(
                "DELETE FROM merch_prices WHERE merch_type = ?",
                (merch_type,)
            )
            await conn.execute(
                f"ALTER TABLE merch DROP COLUMN {merch_type}"
            )
            await conn.commit()
            await message.answer(f"✅ Позиция '{merch_type}' удалена.")
    except Exception as err:
        await message.answer(f"❌ Произошла ошибка при удалении позиции: {err}")
    finally:
        await state.clear()
