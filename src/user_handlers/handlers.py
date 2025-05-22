import logging

from aiogram import F, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot import router
from constants import QUEST_TEXT, SCHOOLS, STATION_PLACE, STATIONS
from src.database.admin import get_admin_level, get_all_admins
from src.database.users import (add_user, check_points, check_st_points,
                                get_all_users, is_quest_started, start_quest)
from src.keyboard import (activity_keyboard, admin_keyboard,
                          continue_quest_keyboard, main_keyboard,
                          mipt_admin_keyboard, pro_admin_keyboard,
                          quest_keyboard, quest_started_keyboard)

# --------------------------------------------------

# /start command and running bot via QR-code

# --------------------------------------------------


@router.message(Command("start"))
async def start_handler(message: types.Message):
    """
    Handle the /start command: регистрирует пользователя, определяет уровень админа
    и показывает соответствующее меню. Приходит параметр после /start — код QR.

    Args:
        message (types.Message): Входящее сообщение с командой /start и опциональным параметром.
    """
    try:
        user = message.from_user
        user_list = await get_all_users()
        if user not in user_list:
            await add_user(message.chat.id, user.username)
        current_username = f"@{user.username}"
        admins = await get_all_admins()
        admin_usernames = [admin[0] for admin in admins]

        logging.info("Пользователь: %s", current_username)

        keyboard = main_keyboard()

        if current_username in admin_usernames:

            admin_level = await get_admin_level(current_username)
            print(f"Уровень админства для {current_username}: {admin_level}")
            if admin_level == 0:
                keyboard = pro_admin_keyboard()
            elif admin_level == 1:
                keyboard = admin_keyboard()
            elif admin_level == 2:
                keyboard = mipt_admin_keyboard()
            await message.answer("🔑 Админ-меню:", reply_markup=keyboard)
        else:
            await add_user(message.chat.id, user.username)
            await message.answer("📌 Выберите действие:", reply_markup=keyboard)

        parts = message.text.split()
        if len(parts) > 1:
            param = parts[1]

            try:
                if int(param[-2:]) >= 10:
                    name = param[-2:]
                else:
                    name = param[-1]
            except ValueError:
                name = param[-1]

            photo_url = f"img/places/{name}.png"
            await do_action(message, photo_url)
    except Exception as err:
        await message.answer(str(err))


async def do_action(message, photo_url):
    """
    Отправляет пользователю фото по заданному URL.

    Args:
        message (types.Message): Сообщение, на которое отвечаем.
        photo_url (str): Путь до файла фото.
    """
    try:
        photo = FSInputFile(photo_url)
        await message.answer_photo(photo, caption="Ваше местоположение:")
    except Exception as err:
        await message.answer(f"Ошибка: {str(err)}")


# --------------------------------------------------

# Lecture schedule

# --------------------------------------------------
@router.message(F.text == "📅 Расписание лекций")
async def send_schedule_photo(message):
    """
    Отправляет пользователю изображение с расписанием лекций.

    Args:
        message (types.Message): Входящее сообщение с запросом расписания.
    """
    try:
        photo = FSInputFile("img/schedule.png")
        await message.answer_photo(photo, caption="📅 Расписание лекций:")
    except Exception as err:
        await message.answer(f"Ошибка: {str(err)}")


# --------------------------------------------------

# Quest

# --------------------------------------------------
@router.message(F.text == "🎯 Квест")
async def quest_handler(message):
    """
    Инициирует квест: выдаёт вступительный текст и клавиатуру.

    Args:
        message (types.Message): Входящее сообщение, запускающее квест.
    """
    if await is_quest_started(message.from_user.username):
        keyboard = quest_started_keyboard()
    else:
        keyboard = quest_keyboard()

    await message.answer(QUEST_TEXT, reply_markup=keyboard)
    await message.answer("Выберите действие:", reply_markup=keyboard)


@router.message(F.text == "▶️ Начать")
async def start_quest_handler(message: types.Message):
    """
    Запускает квест для пользователя и предлагает выбрать станцию.

    Args:
        message (types.Message): Входящее сообщение с командой «Начать».
    """
    await start_quest(message.from_user.username)
    await message.answer("Выберите станцию:", reply_markup=continue_quest_keyboard())


@router.message(F.text == "▶️ Продолжить")
async def continue_quest_handler(message: types.Message):
    """
    Появляется у пользователя, если он уже начал квест

    Args:
        message (types.Message): Входящее сообщение с командой «Продолжить».
    """
    await message.answer("Выберите станцию:", reply_markup=continue_quest_keyboard())


@router.message(F.text == "⬅️ Назад")
async def back_handler(message: types.Message):
    """
    Возвращает пользователя в главное меню.

    Args:
        message (types.Message): Входящее сообщение с командой «Назад».
    """
    await message.answer("Вы снова в главном меню", reply_markup=main_keyboard())


async def send_quest_points(message: types.Message, username: str, station: str):
    """
    Отправляет пользователю общее и по‐станционное количество баллов.

    Args:
        message (types.Message): Сообщение, на которое отвечаем.
        username (str): Имя пользователя.
        station (str): Идентификатор станции.
    """
    points = await check_points(username)
    st_points = await check_st_points(username, station)
    await message.answer(f"Всего баллов: {points}\nБаллы за станцию: {st_points}",
                         reply_markup=quest_started_keyboard())


@router.message(F.text.in_(STATIONS))
async def handle_station(message: types.Message):
    """
    Обрабатывает выбор станции, показывает её расположение и кнопки действия.

    Args:
        message (types.Message): Входящее сообщение с названием станции.
    """
    try:
        station_number = STATIONS[message.text]
        st_place = STATION_PLACE[station_number - 1]
        username = message.from_user.username

        builder = InlineKeyboardBuilder()
        builder.button(text="Код для участия",
                       callback_data=f"code:{username}")
        builder.button(
            text="Баллы", callback_data=f"pts:{username}:{station_number}")

        await message.answer(f"Расположение {message.text}: {st_place}",
                             reply_markup=builder.as_markup())
    except Exception as err:
        await message.answer(str(err))


@router.callback_query(F.data.startswith("code:"))
async def send_code(callback: types.CallbackQuery):
    """
    Показывает пользователю код, который необходимо сообщить на станции
    для проставления баллов

    Args:
        callback (types.CallbackQuery): Объект callback от InlineKeyboard.
    """
    _, username = callback.data.split(":")
    await callback.message.answer(f"Сообщите на станции ваш код: {username}")
    await callback.answer()


@router.callback_query(F.data.startswith("pts:"))
async def send_pts(callback: types.CallbackQuery):
    """
    Показывает пользователю его баллы по запросу.

    Args:
        callback (types.CallbackQuery): Объект callback от InlineKeyboard.
    """
    _, username, station_number = callback.data.split(":")
    await send_quest_points(callback.message, username, station_number)
    await callback.answer()


# --------------------------------------------------

# Map

# --------------------------------------------------
@router.message(F.text == "🗺 Карта")
async def send_map_photo(message: types.Message):
    """
    Отправляет пользователю карту института.

    Args:
        message (types.Message): Входящее сообщение с запросом карты.
    """
    try:
        photo = FSInputFile("img/map.png")
        await message.answer_photo(photo, caption="🗺 Карта института:")
    except Exception as err:
        await message.answer(f"Ошибка: {str(err)}")


# --------------------------------------------------

# Stand locations
# --------------------------------------------------
@router.message(F.text == "📍 Расположение стендов")
async def send_stands_photo(message: types.Message):
    """
    Отправляет изображение с расположением стендов.

    Args:
        message (types.Message): Входящее сообщение с запросом стендов.
    """
    try:
        photo = FSInputFile("img/stand.png")
        await message.answer_photo(photo, caption="📍 Расположение стендов:")
    except Exception as err:
        await message.answer(f"Ошибка: {str(err)}")


# --------------------------------------------------

# SCHOOLS activities

# --------------------------------------------------
@router.message(F.text == "🧩 Активности ФШ")
async def school_handler(message: types.Message):
    """
    Предлагает пользователю выбрать Физтех-школу, активности которой
    он хочет посмотреть.

    Args:
        message (types.Message): Входящее сообщение с запросом активностей.
    """
    await message.answer("Выберите ФШ:", reply_markup=activity_keyboard())


@router.message(F.text.in_(SCHOOLS))
async def handle_activity(message: types.Message):
    """
    Отправляет изображение активностей выбранной школы.

    Args:
        message (types.Message): Входящее сообщение с названием школы.
    """
    try:
        school_number = SCHOOLS[message.text]
        photo = FSInputFile(f"img/activities/{school_number}.png")
        await message.answer_photo(photo)
    except Exception as err:
        await message.answer(f"Ошибка: {str(err)}")
