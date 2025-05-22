import logging

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot import router
from constants import STATIONS
from src.database.admin import get_admin_by_username, get_admin_level
from src.database.users import (get_user_by_username, is_quest_started,
                                update_user_points, update_user_queststation)


class SetPointsStates(StatesGroup):
    """
    FSM-состояния для процесса проставления баллов пользователям.

    waiting_username  — ожидание ввода ника пользователя;
    waiting_station   — ожидание выбора станции;
    waiting_points    — ожидание выбора количества баллов.
    """
    waiting_username = State()
    waiting_station = State()
    waiting_points = State()


@router.message(F.text == "Квест. Проставить баллы")
async def set_points(message: Message, state: FSMContext):
    """
    Начинает диалог проставления баллов.

    Шаг 1: проверяет, что пользователь — администратор уровня 0 или 2.
    Если доступ разрешён — переходит в состояние waiting_username
    и запрашивает ник пользователя.

    Args:
        message (Message): входящее сообщение с текстом команды.
        state (FSMContext): FSM-контекст для хранения данных.
    """
    admin = await get_admin_by_username(f"@{message.from_user.username}")
    level = await get_admin_level(f"@{message.from_user.username}")
    if not admin or level not in (0, 2):
        await message.answer("❌ У вас нет доступа к этой команде.")
        return

    await message.answer("Введите ник пользователя (@username):")
    await state.set_state(SetPointsStates.waiting_username)


@router.message(SetPointsStates.waiting_username)
async def process_username(message: Message, state: FSMContext):
    """
    Обрабатывает ввод ника пользователя.

    Шаг 2:
      - проверяет, что пользователь существует,
      - сохраняет в FSM данные о нике и администраторе,
      - в зависимости от уровня администратора:
          • уровень 0: выдаёт клавиатуру со станциями и
            переходит в waiting_station;
          • уровень 2: сразу переходит к выбору баллов для своей станции.

    Args:
        message (Message): сообщение с ником (например, "@ivan").
        state (FSMContext): FSM-контекст для хранения промежуточных данных.
    """
    username = message.text.strip().lstrip('@')
    user = await get_user_by_username(username)

    if not user:
        await message.answer(f"❌ Пользователь {username} не найден!")
        await state.clear()
        return

    admin = await get_admin_by_username(f"@{message.from_user.username}")

    await state.update_data(username=username, admin=admin)
    level = await get_admin_level(f"@{message.from_user.username}")
    if level == 0:
        builder = InlineKeyboardBuilder()
        for name, number in STATIONS.items():
            builder.button(text=name, callback_data=f"select_station:{number}")
        builder.adjust(2)

        await message.answer("Выберите номер станции:", reply_markup=builder.as_markup())
        await state.set_state(SetPointsStates.waiting_station)
    elif level == 2:
        station_num = await get_admin_level(f'{username}')
        if user.get(f'quest{station_num}_points', 0) != 0:
            await message.answer(f"❌ Пользователю {username} уже начислены баллы.")
            await state.clear()
            return
        await process_points_selection(message, username, admin['questnum'], state)


@router.callback_query(F.data.startswith("select_station:"), SetPointsStates.waiting_station)
async def process_station_selection(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает выбор станции из InlineKeyboard.

    Шаг 3:
      - разбирает номер станции из callback_data,
      - проверяет, что баллы за эту станцию ещё не выставлены,
      - сохраняет station_num в FSM,
      - выводит подтверждение выбора и переходит к выбору количества баллов.

    Args:
        callback (CallbackQuery): callback с данными "select_station:<номер>".
        state (FSMContext): FSM-контекст для хранения данных.
    """
    await callback.answer()
    data = await state.get_data()
    username = data['username']
    station_num = int(callback.data.split(":")[1])

    user = await get_user_by_username(username)
    if user.get(f'quest{station_num}_points', 0) != 0:
        await callback.message.answer(f"❌ Пользователю {username} уже начислены баллы.")
        await state.clear()
        return
    station_name = [name for name,
                    num in STATIONS.items() if num == station_num][0]
    await state.update_data(station_num=station_num)
    await callback.message.answer(f"✅ Вы выбрали {station_name}")
    await process_points_selection(callback.message, username, station_num, state)


async def process_points_selection(message: Message, username: str, station_num: int, state: FSMContext):
    """
    Общий шаг: предлагает выбрать количество баллов (1 или 2).

    Проверяет, начал ли пользователь квест. Если нет — информирует об этом.
    Если да — выводит InlineKeyboard с кнопками "1️⃣", "2️⃣" и "🔙 Назад",
    переходит в состояние waiting_points.

    Args:
        message (Message): сообщение для ответа (либо Message, либо .message из CallbackQuery).
        username (str): ник пользователя (без "@").
        station_num (int): номер выбранной станции.
        state (FSMContext): FSM-контекст для хранения данных.
    """
    if not await is_quest_started(username):
        await message.answer(f"❌ Пользователь {username} ещё не начал квест.")
        return

    await state.update_data(station_num=station_num, username=username)

    builder = InlineKeyboardBuilder()
    builder.button(text="1️⃣", callback_data="points:1")
    builder.button(text="2️⃣", callback_data="points:2")
    builder.button(
        text="🔙 Назад", callback_data=f"back_to_stations:{username}")
    builder.adjust(2)

    await message.answer(
        f"Выберите количество баллов для @{username}:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(SetPointsStates.waiting_points)


@router.callback_query(F.data.startswith("back_to_stations:"), SetPointsStates.waiting_points)
async def back_to_stations(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает нажатие кнопки "🔙 Назад" при выборе баллов.

    Удаляет текущее сообщение и возвращает пользователя
    к этапу выбора станции (waiting_station).

    Args:
        callback (CallbackQuery): callback с данными "back_to_stations:<username>".
        state (FSMContext): FSM-контекст для хранения данных.
    """
    try:
        await callback.message.delete()

        username = callback.data.split(":")[1]
        await state.update_data(username=username)

        builder = InlineKeyboardBuilder()
        for name, number in STATIONS.items():
            builder.button(
                text=name,
                callback_data=f"select_station:{number}"
            )
        builder.adjust(2)

        await callback.message.answer(
            text=f"🔙 Возврат к выбору станции для @{username}",
            reply_markup=builder.as_markup()
        )

        await state.set_state(SetPointsStates.waiting_station)

    except Exception as err:
        logging.error("Ошибка в back_to_stations: %s", err)
        await callback.answer("⚠️ Произошла ошибка!", show_alert=True)


@router.callback_query(F.data.startswith("points:"), SetPointsStates.waiting_points)
async def process_points_callback(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает выбор количества баллов.

    Шаг 4:
      - разбирает выбранное количество баллов из callback_data,
      - обновляет баллы пользователя в БД,
      - информирует об успешном начислении и сбрасывает FSM.

    Args:
        callback (CallbackQuery): callback с данными "points:<1 или 2>".
        state (FSMContext): FSM-контекст для хранения данных.
    """
    await callback.answer()
    points = int(callback.data.split(":")[1])
    data = await state.get_data()

    try:
        await update_user_points(data['username'], data['station_num'], points)
        await update_user_queststation(data['username'])
    except Exception as err:
        await callback.message.answer(err)

    await callback.message.answer(
        f"✅ Пользователю {data['username']} начислено {points} баллов!"
    )
    await state.clear()
