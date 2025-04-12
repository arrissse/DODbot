from bot import bot, dp, router
from aiogram import Bot, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import FSInputFile

from keyboard import main_keyboard, admin_keyboard, pro_admin_keyboard, mipt_admin_keyboard, quest_keyboard, quest_started_keyboard, continue_quest_keyboard, activity_keyboard
from users import add_user, start_quest, is_quest_started, check_points, check_st_points, get_user_by_username, get_all_users
from admin import get_all_admins, add_admin, get_admin_level
from aiogram.types import BotCommand
import logging

stations = {
    "станция ФРКТ": 1,
    "станция ЛФИ": 2,
    "станция ФАКТ": 3,
    "станция ФЭФМ": 4,
    "станция ФПМИ": 5,
    "станция ФБМФ": 6,
    "станция КНТ": 7,
    "станция ФБВТ": 8,
    "станция ВШПИ": 9,
    "станция ВШМ": 10,
    "станция ПИШ РПИ": 11
}

station_place = [
    "Физтех.Цифра 3 этаж",
    "Лабораторный корпус",
    "Физтех.Арктика 2 этаж",
    "Физтех.Арктика 3 этаж",
    "Главный корпус 1 этаж",
    "Физтех.Цифра 4 этаж",
    "Физтех.Цифра 2 этаж",
    "Главный корпус 1 этаж",
    "Главный корпус 2 этаж",
    "Главный корпус 1 этаж",
    "Физтех.Арктика 4 этаж"
]

schools = {
    "ФРКТ": 1,
    "ЛФИ": 2,
    "ФАКТ": 3,
    "ФЭФМ": 4,
    "ФПМИ": 5,
    "ФБМФ": 6,
    "КНТ": 7,
    "ФБВТ": 8,
    "ВШПИ": 9,
    "ВШМ": 10,
    "ПИШ РПИ": 11
}

'''
-----------------------

Старт + обработка QR-кодов

-----------------------
'''


@router.message(Command("start"))
async def start_handler(m: types.Message):
 try:
    user = m.from_user
    user_list = await get_all_users()
    logging.info(user_list)
    if not user in user_list: 
        await add_user(m.chat.id, user.username)
    current_username = f"@{user.username}"
    admins = await get_all_admins()
    admin_usernames = [admin[0] for admin in admins]
    logging.info(admin_usernames)

    logging.info(f"Список админов: {admin_usernames}")
    logging.info(f"Пользователь: {current_username}")

    keyboard = main_keyboard()
    commands = [BotCommand(command="start", description="Перезапустить бота")]
    await bot.set_my_commands(commands)

    if current_username in admin_usernames:

        admin_level = await get_admin_level(current_username)
        print(f"Уровень админства для {current_username}: {admin_level}")
        if admin_level == 0:
            keyboard = pro_admin_keyboard()
        elif admin_level == 1:
            keyboard = admin_keyboard()
        elif admin_level == 2:
            keyboard = mipt_admin_keyboard()
        await m.answer("🔑 Админ-меню:", reply_markup=keyboard)
    else:
        await add_user(m.chat.id, user.username)
        await m.answer("📌 Выберите действие:", reply_markup=keyboard)

    parts = m.text.split()
    if len(parts) > 1:
        param = parts[1]

        try:
            if int(param[-2:]) >= 10:
                name = param[-2:]
            else:
                name = param[-1]
        except ValueError:
            name = param[-1]

        photo_url = f"img/{name}.png"
        await do_action(m, photo_url)
 except Exception as e:
     await m.answer(str(e))


async def do_action(message, photo_url):
    try:
        photo = FSInputFile(photo_url)
        await message.answer_photo(photo, caption="Ваше местоположение:")
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")

'''
-----------------------

Расписание лекций

-----------------------
'''


@router.message(F.text == "📅 Расписание лекций")
async def send_schedule_photo(m):
    try:
       photo = FSInputFile("img/schedule.png")
       await m.answer_photo(photo, caption="📅 Расписание лекций:")
    except Exception as e:
        await m.answer(f"Ошибка: {str(e)}")


'''
-----------------------

Квест

-----------------------
'''


@router.message(F.text == "🎯 Квест")
async def quest_handler(message):
    if await is_quest_started(message.from_user.username):
        keyboard = quest_started_keyboard()
    else:
        keyboard = quest_keyboard()
    await message.answer("*Описание квеста*", reply_markup=keyboard)
    await message.answer("Выберите действие:", reply_markup=keyboard)


@router.message(F.text == "▶️ Начать")
async def start_quest_handler(message: types.Message):
    await start_quest(message.from_user.username)
    await message.answer("Выберите станцию:", reply_markup=continue_quest_keyboard())


@router.message(F.text == "▶️ Продолжить")
async def continue_quest_handler(message: types.Message):
    await message.answer("Выберите станцию:", reply_markup=continue_quest_keyboard())


@router.message(F.text == "⬅️ Назад")
async def back_handler(message: types.Message):
    await message.answer("Вы снова в главном меню", reply_markup=main_keyboard())


async def send_quest_points(message: types.Message, username: str, station: str):
    points = await check_points(username)
    st_points = await check_st_points(username, station)
    await message.answer(f"Всего баллов: {points}\nБаллы за станцию: {st_points}", reply_markup=quest_started_keyboard())

@router.message(F.text.in_(stations))
async def handle_station(message: types.Message):
    try:
        station_number = stations[message.text]
        st_place = station_place[station_number - 1]
        username = message.from_user.username

        builder = InlineKeyboardBuilder()
        builder.button(text="Код для участия",
                       callback_data=f"code:{username}")
        builder.button(
            text="Баллы", callback_data=f"points:{username}:{station_number}")

        await message.answer(f"Расположение {message.text}: {st_place}", reply_markup=builder.as_markup())
    except Exception as e:
        await message.answer(str(e))


@router.callback_query(F.data.startswith("code:"))
async def send_code(callback: types.CallbackQuery):
    _, username = callback.data.split(":")
    await callback.message.answer(f"Сообщите на станции ваш код: {username}")
    await callback.answer()


@router.callback_query(F.data.startswith("points:"))
async def send_pts(callback: types.CallbackQuery):
    _, username, station_number = callback.data.split(":")
    await send_quest_points(callback.message, username, station_number)
    await callback.answer()


'''
-----------------------

Карта

-----------------------
'''


@router.message(F.text == "🗺 Карта")
async def send_map_photo(message: types.Message):
    try:
        photo = FSInputFile("img/map.png")
        await message.answer_photo(photo, caption="🗺 Карта института:")
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")


'''
-----------------------

Расположение стендов

-----------------------
'''


@router.message(F.text == "📍 Расположение стендов")
async def send_stands_photo(message: types.Message):
    try:
        photo = FSInputFile("img/stand.png")
        await message.answer_photo(photo, caption="📍 Расположение стендов:")
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")


'''
-----------------------

Активности ФШ

-----------------------
'''

@router.message(F.text == "🧩 Активности ФШ")
async def school_handler(message: types.Message):
    await message.answer("Выберите ФШ:", reply_markup=activity_keyboard())


@router.message(F.text.in_(schools))
async def handle_activity(message: types.Message):
    try:
        school_number = schools[message.text]
        photo = FSInputFile(f"img/activities/{school_number}.png")
        await message.answer_photo(photo)
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")
