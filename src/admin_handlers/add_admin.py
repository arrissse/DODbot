from aiogram import F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot import router
from constants import STATIONS
from src.database.admin import (add_admin, get_admin_by_username,
                                get_admin_level, update_admin_questnum)
from src.database.users import get_user_by_username


class AdminStates(StatesGroup):
    """
    FSM-состояния для создания администратора.

    waiting_username  — ожидание ввода ника нового администратора;
    waiting_level     — ожидание ввода уровня админства (0, 1 или 2);
    waiting_station   — (только для уровня 2) ожидание выбора номера станции.
    """
    waiting_username = State()
    waiting_level = State()
    waiting_station = State()


@router.message(F.text == "Добавить админа")
async def new_admin(message: types.Message, state: FSMContext):
    """
    Шаг 1: запускает диалог добавления админа.

    Проверяет, что отправитель уже является админом уровня 0.
    Если да — запрашивает ник пользователя и переводит FSM в состояние waiting_username.
    Иначе — сообщает об отказе в доступе.

    Args:
        message (types.Message): входящее сообщение с текстом "Добавить админа".
        state (FSMContext): FSM-контекст для хранения промежуточных данных.
    """
    user = await get_admin_by_username('@' + message.from_user.username)
    level = await get_admin_level(user)
    if user is not None and level == 0:
        await message.answer("Введите ник пользователя (@username):")
        await state.set_state(AdminStates.waiting_username)
    else:
        await message.answer("❌ У вас нет доступа к этой команде.")


@router.message(AdminStates.waiting_username)
async def process_name(message: types.Message, state: FSMContext):
    """
    Шаг 2: обрабатывает введённый ник нового администратора.

    Сохраняет введённый ник в FSM и запрашивает уровень админства:
    0 — полный доступ, 1 — выдача мерча, 2 — админ конкретной станции.

    Args:
        message (types.Message): сообщение с ником (@username).
        state (FSMContext): FSM-контекст.
    """
    username = message.text

    await state.update_data(username=username)
    await message.answer("Введите уровень админства (0 - pro-admin, 1 - выдача мерча, 2 - админ фш):")
    await state.set_state(AdminStates.waiting_level)


@router.message(AdminStates.waiting_level)
async def process_level(message: types.Message, state: FSMContext):
    """
    Шаг 3: обрабатывает ввод уровня админства.

    Если уровень некорректен — отменяет FSM.
    При level 2 выводит клавиатуру выбора станции и переводит в waiting_station.
    При level 0 или 1 вызывает process_admin_creation и завершает FSM.

    Args:
        message (types.Message): сообщение с числом 0, 1 или 2.
        state (FSMContext): FSM-контекст.

    Returns:
        None
    """
    try:
        admin_level = int(message.text)
        if admin_level not in {0, 1, 2}:
            raise ValueError
    except ValueError:
        await message.answer("❌ Некорректный уровень админства. Используйте 0, 1 или 2.")
        return await state.clear()

    data = await state.get_data()
    username = data['username']

    if admin_level == 2:
        builder = InlineKeyboardBuilder()
        for name, number in STATIONS.items():
            builder.button(
                text=name,
                callback_data=f"select_station:{number}:{username}:{admin_level}"
            )
        builder.adjust(2)
        await message.answer(
            "Выберите номер станции админа:",
            reply_markup=builder.as_markup()
        )
        await state.set_state(AdminStates.waiting_station)
    else:
        await process_admin_creation(message, username, admin_level)
        await state.clear()


@router.callback_query(F.data.startswith("select_station:"), AdminStates.waiting_station)
async def process_number(callback: types.CallbackQuery, state: FSMContext):
    """
    Шаг 4 (для level 2): обрабатывает выбор станции из InlineKeyboard.

    Из callback_data извлекаются number, username и admin_level.
    Вызывает process_admin_creation, записывает station_num в БД
    и подтверждает успешное назначение.

    Args:
        callback (types.CallbackQuery): callback с данными "select_station:<num>:<username>:<level>".
        state (FSMContext): FSM-контекст.
    """
    _, number, username, admin_level = callback.data.split(':')

    try:
        await process_admin_creation(callback.message, username, admin_level)
        await update_admin_questnum(username, int(number))
        await callback.message.answer(
            f"✅ Админу {username} назначена станция №{number}."
        )
    except Exception as err:
        await callback.message.answer(f"❌ Ошибка: {str(err)}")

    await state.clear()


async def process_admin_creation(message: types.Message, username: str, admin_level: int):
    """
    Общая функция для создания записи администратора в базе.

    Вызывает add_admin(username, admin_level), отправляет подтверждение
    и уведомление пользователю (если он есть в системе).

    Args:
        message (types.Message): объект для ответных сообщений.
        username (str): ник нового администратора (с "@").
        admin_level (int): уровень прав (0, 1 или 2).
    """
    try:
        await add_admin(username, admin_level)
        await message.answer(
            f"✅ Админ {username} уровня {admin_level} добавлен."
        )
        user = await get_user_by_username(username.lstrip('@'))
        if user:
            await message.bot.send_message(
                user['id'],
                "Вас назначили админом. Для доступа к меню используйте /start"
            )

    except Exception as err:
        await message.answer(f"❌ Ошибка: {str(err)}")
