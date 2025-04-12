from bot import bot, dp, router
from aiogram import F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from users import get_all_users, get_user_by_username
from handlers import stations
from admin import add_admin, get_all_admins, get_admin_by_username, update_admin_questnum, update_admin_info, get_admin_level


class AdminStates(StatesGroup):
    waiting_username = State()
    waiting_level = State()
    waiting_station = State()


@router.message(F.text == "Добавить админа")
async def new_admin(message: types.Message, state: FSMContext):
    user = await get_admin_by_username('@' + message.from_user.username)
    level = await get_admin_level(user)
    if user is not None and level == 0:
        await message.answer("Введите ник пользователя (@username):")
        await state.set_state(AdminStates.waiting_username)
    else:
        await message.answer("❌ У вас нет доступа к этой команде.")


@router.message(AdminStates.waiting_username)
async def process_name(message: types.Message, state: FSMContext):
    username = message.text.lstrip('@')
    users = await get_all_users()
    admins = await get_all_admins()

    user_exists = any(user['username'] == username for user in users)
    if not user_exists:
        await message.answer(f"❌ Пользователь @{username} не найден в списке.")
        return await state.clear()

    admin_exists = any(admin['adminname'] == username for admin in admins)
    if admin_exists:
        await message.answer(f"Пользователь @{username} уже является админом.")
        return await state.clear()

    await state.update_data(username=username)
    await message.answer("Введите уровень админства (0 - pro-admin, 1 - выдача мерча, 2 - админ фш):")
    await state.set_state(AdminStates.waiting_level)


@router.message(AdminStates.waiting_level)
async def process_level(message: types.Message, state: FSMContext):
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
        for name, number in stations.items():
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
    _, number, username, admin_level = callback.data.split(':')

    try:
        await update_admin_questnum(username, int(number))
        await callback.message.answer(
            f"✅ Админу @{username} назначена станция №{number}."
        )
        await process_admin_creation(callback.message, username, int(admin_level))
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {str(e)}")

    await state.clear()


async def process_admin_creation(message: types.Message, username: str, admin_level: int):
    try:
        user = await get_user_by_username(username)

        if user:
            await message.bot.send_message(
                user['id'],
                "Вас назначили админом. Для доступа к меню используйте /start"
            )

        admins = await get_all_admins()
        admin_list = "\n".join([f"@{a.username}" for a in admins])
        await message.answer(f"{msg}\nСписок админов:\n{admin_list}")

    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
