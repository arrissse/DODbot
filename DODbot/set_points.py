from bot import bot, dp, router
from aiogram import Bot, types, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from users import update_user_points, get_user_by_username, is_quest_started, update_user_queststation
from admin import get_admin_by_username, get_admin_level
from handlers import stations
from keyboard import main_keyboard
import logging


class SetPointsStates(StatesGroup):
    waiting_username = State()
    waiting_station = State()
    waiting_points = State()


@router.message(F.text == "Квест. Проставить баллы")
async def set_points(message: Message, state: FSMContext):
    admin = await get_admin_by_username(f"@{message.from_user.username}")
    level = await get_admin_level(f"@{message.from_user.username}")
    if not admin or (level != 0 and level != 2):
        await message.answer("❌ У вас нет доступа к этой команде.")
        return

    await state.set_state(SetPointsStates.waiting_username)
    await message.answer("Введите ник пользователя (@username):")


@router.message(SetPointsStates.waiting_username)
async def process_username(message: Message, state: FSMContext):
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
        for name, number in stations.items():
            builder.button(text=name, callback_data=f"select_station:{number}")
        builder.adjust(2)

        await message.answer("Выберите номер станции:", reply_markup=builder.as_markup())
        await state.set_state(SetPointsStates.waiting_station)
    elif level == 2:
        if user.stations[admin.quest_num] != 0:
            await message.answer(f"❌ Пользователю {username} уже начислены баллы.")
            await state.clear()
            return
        await process_points_selection(message, username, admin.quest_num, user)


@router.callback_query(F.data.startswith("select_station:"), SetPointsStates.waiting_station)
async def process_station_selection(callback: CallbackQuery, state: FSMContext):
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
                    num in stations.items() if num == station_num][0]
    await state.update_data(station_num=station_num)
    await callback.message.answer(f"✅ Вы выбрали {station_name}")
    await process_points_selection(callback.message, username, station_num, user, state)


async def process_points_selection(message: Message, username: str, station_num: int, user, state: FSMContext):
    if not await is_quest_started(username):
        await message.answer(f"❌ Пользователь {username} ещё не начал квест.")
        return

    await state.update_data(station_num=station_num, username=username)

    builder = InlineKeyboardBuilder()
    builder.button(text="1️⃣", callback_data=f"points:1")
    builder.button(text="2️⃣", callback_data=f"points:2")
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
    try:
        await callback.message.delete()

        username = callback.data.split(":")[1]
        await state.update_data(username=username)

        builder = InlineKeyboardBuilder()
        for name, number in stations.items():
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

    except Exception as e:
        logging.error(f"Ошибка в back_to_stations: {e}")
        await callback.answer("⚠️ Произошла ошибка!", show_alert=True)


@router.callback_query(F.data.startswith("points:"), SetPointsStates.waiting_points)
async def process_points_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    points = int(callback.data.split(":")[1])
    data = await state.get_data()

    try:
        await update_user_points(data['username'], data['station_num'], points)
        await update_user_queststation(data['username'])
    except Exception as e:
        await callback.message.answer(e)

    await callback.message.answer(
        f"✅ Пользователю {data['username']} начислено {points} баллов!"
    )
    await state.clear()
