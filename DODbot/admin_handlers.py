from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot import bot, dp, router
from aiogram import Bot, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from datetime import datetime
from keyboard import main_keyboard, pro_admin_merch, pro_admin_keyboard, pro_admin_quiz_start
from users import save_users_to_excel, count_active_quests, get_user_by_username
from users import count_finished_quests, check_points, update_merch_points
from admin import save_admins_to_excel, get_admin_by_username, get_admin_level
from merch import give_merch, is_got_merch, got_merch, add_column, save_merch_to_excel
from quiz import update_quiz_time
from database import db_manager
from aiogram.fsm.state import State, StatesGroup
import logging
from urllib.parse import quote, unquote
from aiogram.utils.callback_answer import CallbackData


class Form(StatesGroup):
    waiting_username = State()
    waiting_merch_type = State()
    waiting_new_price = State()
    waiting_merch_name = State()
    waiting_merch_cost = State()
    waiting_delete_merch = State()
    edit_price = State()


'''
-----------------------
admins
-----------------------
'''


@router.message(Command("admins"))
async def send_admins_list(message: Message):
    user = await get_admin_by_username(f'@{message.from_user.username}')
    level = await get_admin_level(f'@{message.from_user.username}') if user else None

    if user and level == 0:
        filename = await save_admins_to_excel(bot=bot)
        print(f"Файл Excel создан: {filename}")

        if filename:
            await message.answer_document(FSInputFile(filename))
        else:
            await message.answer("❌ В базе данных нет пользователей.")
    else:
        await message.answer("❌ У вас нет доступа к этой команде.")


'''
-----------------------
merch
-----------------------
'''


@router.message(Command("merch"))
async def send_merch_list(message: Message):
    user = await get_admin_by_username(f'@{message.from_user.username}')
    level = await get_admin_level(f'@{message.from_user.username}') if user else None

    if user and level == 0:
        filename = await save_merch_to_excel()
        print(f"Файл Excel создан: {filename}")

        if filename:
            await message.answer_document(FSInputFile(filename))
        else:
            await message.answer("❌ База данных пуста.")
    else:
        await message.answer("❌ У вас нет доступа к этой команде.")


'''
-----------------------
Мерч
-----------------------
'''


@router.message(F.text == "Мерч")
async def pro_admin_merch_button(message: Message):
    user = await get_admin_by_username(f'@{message.from_user.username}')
    level = await get_admin_level(f'@{message.from_user.username}') if user else None

    try:
        if user and level == 0:
            await message.answer("Выберите действие:", reply_markup=pro_admin_merch())
        else:
            await message.answer("❌ У вас нет доступа к этой команде.")
    except Exception as e:
        await message.answer(str(e))


'''
-----------------------
Назад
-----------------------
'''


@router.message(F.text == "Назад ⬅️")
async def pro_admin_merch_back(message: Message):
    user = await get_admin_by_username(f'@{message.from_user.username}')
    level = await get_admin_level(f'@{message.from_user.username}') if user else None
    try:
        if user and level == 0:
            await message.answer("🔑 Админ-меню:", reply_markup=pro_admin_keyboard())
        else:
            await message.answer("❌ У вас нет доступа к этой команде.")
    except Exception as e:
        await message.answer(str(e))


'''
-----------------------
Начать квиз
-----------------------
'''


@router.message(F.text == "Начать квиз")
async def pro_admin_quiz_button(message: Message):
    user = await get_admin_by_username(f'@{message.from_user.username}')
    level = await get_admin_level(f'@{message.from_user.username}') if user else None

    try:
        if user and level == 0:
            await message.answer("Выберите квиз:", reply_markup=pro_admin_quiz_start())
        else:
            await message.answer("❌ У вас нет доступа к этой команде.")
    except Exception as e:
        await message.answer(str(e))


quiz_list = {
    "Квиз 1": 1,
    "Квиз 2": 2,
    "Квиз 3": 3,
    "Квиз 4": 4,
    "Квиз 5": 5,
}


@router.message(F.text.in_(quiz_list))
async def handle_quiz_start(message: Message):
    quiz_number = quiz_list[message.text]
    markup = InlineKeyboardBuilder()
    markup.button(InlineKeyboardButton("Да", callback_data=f'start_quiz:{quiz_number}'),
                  InlineKeyboardButton("Нет", callback_data='not_start_quiz:'))
    await message.answer(f"Начать {message.text}?", reply_markup=markup.as_markup())


@router.callback_query(F.data.startswith("start_quiz:"))
async def start_quiz(call: CallbackQuery):
    try:
        await call.answer()
        _, quiz_id = call.data.split(":")
        quiz_id = int(quiz_id)
        async with db_manager.get_connection() as conn:
            quiz_info = await conn.fetchrow(
                "SELECT * FROM quiz_schedule WHERE id = ?",
                (quiz_id, )
            )
        if not quiz_info:
            return await call.message.answer("Ошибка: квиз не найден.")
        quiz_name = quiz_info[0]
        current_time = datetime.now().strftime("%H:%M")
        await update_quiz_time(quiz_id, current_time)
        markup = InlineKeyboardBuilder()
        markup.button(InlineKeyboardButton("Отправить первый вопрос",
                                           callback_data=f'next_question:{quiz_id}:1'))
        await call.message.answer(f"✅ {quiz_name} начат!", reply_markup=markup.as_markup())
    except Exception as e:
        await call.message.answer(f"❌ {str(e)}")


@router.callback_query(F.data.startswith("next_question:"))
async def send_next_question(call: CallbackQuery):
    return


@router.callback_query(F.data.startswith("answer:"))
async def check_answer(call: CallbackQuery):
    await call.answer()
    _, question_id, answer_id = call.data.split(":")
    question_id, answer_id = int(question_id), int(answer_id)
    async with db_manager.get_connection() as conn:
        result = await conn.fetchrow(
            "SELECT is_correct FROM answers WHERE id = ?",
            (answer_id, )
        )
    if result and result['is_correct']:
        await call.message.answer("✅ Верно!")
    else:
        await call.message.answer("❌ Неверно.")


@router.callback_query(F.data.startswith("not_start_quiz"))
async def cancel_quiz(call: CallbackQuery):
    await call.answer("❌ Операция отменена.")
    await call.message.answer("❌ Операция отменена.")


'''
-----------------------
Таблица пользователей
-----------------------
'''


@router.message(F.text == "Таблица пользователей")
async def send_users_list(message: Message):
    user = await get_admin_by_username(f'@{message.from_user.username}')
    if user:
        filename = await save_users_to_excel()
        if filename:
            await message.answer_document(FSInputFile(filename))
        else:
            await message.answer("❌ В базе данных нет пользователей.")
    else:
        await message.answer("❌ У вас нет доступа к этой команде.")


'''
-----------------------
Переключить меню
-----------------------
'''


@router.message(F.text == "Переключить меню")
async def chage_menu(m: Message):
    await m.answer("Для повторного переключения меню введите /start", reply_markup=main_keyboard())


'''
-----------------------
Квест. Текущая статистика
-----------------------
'''


@router.message(F.text == "Квест. Текущая статистика")
async def statistics(message: Message):
    user = await get_admin_by_username(f'@{message.from_user.username}')
    if user:
        active_users = await count_active_quests()
        finished_users = await count_finished_quests()
        await message.answer(f"Количество пользователей, начавших квест: {active_users}\n"
                             f"Количество пользователей, завершивших квест: {finished_users}\n")
    else:
        await message.answer("❌ У вас нет доступа к этой команде.")


'''
-----------------------
Стоимость мерча
-----------------------
'''


async def create_price_table():
    async with db_manager.get_connection() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS merch_prices (
                merch_type TEXT PRIMARY KEY,
                price INTEGER DEFAULT 0
            )
        """)
        await conn.execute("""
            INSERT INTO merch_prices (merch_type, price) VALUES 
                ('Раскрасить шоппер', 5),
                ('Шоппер', 6),
                ('Раскрасить футболку', 7),
                ('Футболка', 8),
                ('Пауэрбанк', 15)
            ON CONFLICT (merch_type) DO NOTHING
        """)
        await conn.commit()


async def get_merch_types():
    async with db_manager.get_connection() as conn:
        cursor = await conn.execute("SELECT merch_type FROM merch_prices")
        result = await cursor.fetchall()
        return [row['merch_type'] for row in result]


async def get_merch_price(merch_type: str):
    async with db_manager.get_connection() as conn:
       async with conn.execute(
           "SELECT price FROM merch_prices WHERE merch_type = ?",
           (merch_type,)
       ) as cursor:
           result = await cursor.fetchone()
           return result[0] if result else None


async def update_merch_price(merch_type, new_price):
    async with db_manager.get_connection() as conn:
        await conn.execute("""
            INSERT INTO merch_prices (merch_type, price) 
            VALUES (?, ?)
            ON CONFLICT (merch_type) DO UPDATE SET price = ?
        """, (merch_type, new_price, new_price))
        await conn.commit()


@router.message(F.text == "Стоимость мерча")
async def merch_prices_menu(message: Message):
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
    await call.answer()
    merch_type = call.data.split(":")[1]
    await state.update_data(merch_type=merch_type)
    await state.set_state(Form.edit_price)
    current_price = await get_merch_price(merch_type)
    await call.message.answer(f"Текущая стоимость {merch_type}: {current_price}\nВведите новую стоимость:")


@router.message(Form.edit_price)
async def process_new_price(message: Message, state: FSMContext):
    data = await state.get_data()
    merch_type = data['merch_type']
    try:
        new_price = int(message.text)
        await update_merch_price(merch_type, new_price)
        await message.answer(f"✅ Стоимость {merch_type} обновлена до {new_price}!")
    except ValueError:
        await message.answer("❌ Ошибка! Введите корректное число.")
    await state.clear()


'''
-----------------------
Выдать мерч
-----------------------
'''

@router.message(F.text == "Выдать мерч")
async def give_merch_to_user(message: Message, state: FSMContext):
    user = await get_admin_by_username(f'@{message.from_user.username}')
    if user and (user[1] == 0 or user[1] == 1):
        await message.answer("Введите ник пользователя (@username):")
        await state.set_state(Form.waiting_username)
    else:
        await message.answer("❌ У вас нет доступа к этой команде.")


merch_callback = CallbackData("give_merch", "price", "merch_type", "username")


@router.message(Form.waiting_username)
async def process_fusername(m: Message, state: FSMContext):
    try:
        # Проверка формата username
        if not m.text.startswith('@'):
            await m.answer("❌ Введите ник в формате @username")
            return

        username = m.text.lstrip('@')

        # Проверка наличия пользователя
        if not await get_user_by_username(username):
            await m.answer(f"❌ Пользователь @{username} не найден")
            return

        # Проверка получения мерча
        if await is_got_merch(username):
            await m.answer(f"❌ Пользователь @{username} уже получил мерч")
            return

        await state.update_data(username=username)
        user_points = await check_points(username)
        markup = InlineKeyboardBuilder()
        merch_types = await get_merch_types()

        # Формируем кнопки
        for merch in merch_types:
            try:
                price = await get_merch_price(merch)
                if user_points >= price and not await got_merch(username, merch):
                    # Заменяем пробелы в названии мерча
                    safe_merch = merch.replace(" ", "_")
                    # Генерируем безопасный callback_data
                    callback_data = merch_callback.new(
                        price=str(price),
                        merch_type=safe_merch,
                        username=username
                    )
                    markup.add(InlineKeyboardButton(
                        text=f"{merch} - {price} баллов",
                        callback_data=callback_data
                    ))
            except Exception as e:
                logging.error(f"Ошибка обработки мерча {merch}: {str(e)}")

        markup.adjust(1)
        if markup.as_markup().inline_keyboard:
            await m.answer(
                f"🏆 Баллы пользователя @{username}: {user_points}\n"
                "Выберите мерч для выдачи:",
                reply_markup=markup.as_markup()
            )
        else:
            await m.answer(f"⚠️ У пользователя @{username} недостаточно баллов ({user_points})")

        await state.clear()

    except Exception as e:
        logging.error(f"Ошибка в process_fusername: {str(e)}")
        await m.answer("❌ Произошла ошибка обработки запроса")
        await state.clear()


# Обработчик колбэка
@router.callback_query(merch_callback.filter())
async def process_merch_selection(
    call: CallbackQuery,
    callback_data: dict,
    bot: Bot
):
    try:
        # Извлекаем параметры
        price = int(callback_data["price"])
        merch_type = callback_data["merch_type"].replace(
            "_", " ")  # Восстанавливаем пробелы
        username = callback_data["username"]

        # Подтверждение выдачи
        confirm_markup = InlineKeyboardBuilder()
        confirm_markup.row(
            InlineKeyboardButton(
                text="✅ Подтвердить",
                callback_data=merch_callback.new(
                    price=price,
                    merch_type=merch_type.replace(" ", "_"),
                    username=username
                )
            ),
            InlineKeyboardButton(
                text="❌ Отменить",
                callback_data="cancel_merch"
            )
        )

        await call.message.edit_text(
            f"Вы уверены, что хотите выдать:\n"
            f"👤 Пользователь: @{username}\n"
            f"🎁 Мерч: {merch_type}\n"
            f"🏅 Стоимость: {price} баллов",
            reply_markup=confirm_markup.as_markup()
        )

    except Exception as e:
        logging.error(f"Ошибка в process_merch_selection: {str(e)}")
        await call.answer("❌ Ошибка обработки выбора")


@router.callback_query(F.data == "cancel_merch")
async def cancel_merch_selection(call: CallbackQuery):
    await call.message.delete()
    await call.answer("❌ Выдача отменена")
'''
-----------------------
Добавить позицию мерча
-----------------------
'''


@router.message(F.text == "Добавить позицию мерча")
async def add_merch_type(message: Message, state: FSMContext):
    user = await get_admin_by_username(f'@{message.from_user.username}')
    if user and user[1] == 0:
        await message.answer("Введите название новой позиции мерча:")
        await state.set_state(Form.waiting_merch_name)
    else:
        await message.answer("❌ У вас нет доступа к этой команде.")


@router.message(Form.waiting_merch_name)
async def process_type(message: Message, state: FSMContext):
    await state.update_data(type=message.text)
    await message.answer("Введите стоимость новой позиции мерча:")
    await state.set_state(Form.waiting_merch_cost)


@router.message(Form.waiting_merch_cost)
async def process_type_cost(message: Message, state: FSMContext):
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
    except Exception as e:
        await message.answer(f"❌ Ошибка при добавлении колонки: {e}")
        await state.clear()
        return
    await message.answer(f"✅ Позиция '{merch_type}' добавлена с ценой {cost} баллов.")
    await state.clear()


'''
-----------------------
Удалить позицию мерча
-----------------------
'''


@router.message(F.text == "Удалить позицию мерча")
async def remove_merch_type(message: Message, state: FSMContext):
    user = await get_admin_by_username(f'@{message.from_user.username}')
    if user and user[1] == 0:
        await message.answer("Введите название позиции мерча, которую необходимо удалить:")
        await state.set_state(Form.waiting_delete_merch)
    else:
        await message.answer("❌ У вас нет доступа к этой команде.")


@router.message(Form.waiting_delete_merch)
async def process_r_type(message: Message, state: FSMContext):
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
            # ВНИМАНИЕ: Вызов DROP COLUMN в SQLite может быть недоступен.
            await conn.execute(
                f"ALTER TABLE merch DROP COLUMN {merch_type}"
            )
            await conn.commit()
            await message.answer(f"✅ Позиция '{merch_type}' удалена.")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при удалении позиции: {e}")
    finally:
        await state.clear()
