from bot import bot, router, dp
from aiogram import F
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboard import main_keyboard
from users import update_quize_points, is_finished_quiz, check_quiz_points
from datetime import datetime
import random
from database import db_manager


from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db_manager
from datetime import datetime
import random


class QuizStates(StatesGroup):
    waiting_code = State()


async def create_quiz_table():
    async with db_manager.get_connection() as conn:
        cursor = await conn.cursor()

        # Создание таблиц
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_name TEXT NOT NULL,
                start_time TEXT CHECK (LENGTH(start_time) = 5 AND start_time LIKE '__:__'),
                location TEXT NOT NULL,
                is_started INTEGER DEFAULT 0
            )
        """)

        # Инициализация данных
        await cursor.execute("""
            INSERT OR IGNORE INTO quiz_schedule (quiz_name, start_time, location) VALUES 
                ("История мфти", "11:00", "2.36 Физтех.Цифра"),
                ("Физтех шутят", "12:00", "2.36 Физтех.Цифра"),
                ("Физика не для слабонервных", "13:00", "2.36 Физтех.Цифра"),
                ("Математика не для слабонервных", "14:00", "2.36 Физтех.Цифра"),
                ("Квиз 5", "15:00", "305 ЛК")
        """)

        # Создание таблицы вопросов
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id INTEGER NOT NULL,
                question_number INTEGER NOT NULL,
                text TEXT DEFAULT 'Вопрос без текста', 
                UNIQUE(quiz_id, question_number),
                FOREIGN KEY (quiz_id) REFERENCES quiz_schedule(id)
            )
        """)

        # Создание таблицы ответов
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS answers(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                answer_text TEXT NOT NULL,
                is_correct INTEGER DEFAULT 0,
                FOREIGN KEY(question_id) REFERENCES questions(id)
            )
        """)

        # Генерация вопросов и ответов
        cursor = await conn.execute("SELECT id FROM quiz_schedule")
        rows = await cursor.fetchall()
        quiz_ids = [row[0] for row in rows]

        for quiz_id in quiz_ids:
            for question_number in range(1, 26):
                await cursor.execute("""
                    INSERT OR IGNORE INTO questions (quiz_id, question_number, text)
                    VALUES (?, ?, ?)
                """, (quiz_id, question_number, f"Вопрос {question_number} для квиза {quiz_id}"))

                question_row = await cursor.execute("""
                    SELECT id FROM questions WHERE quiz_id = ? AND question_number = ?
                """, (quiz_id, question_number))
                question_row = await question_row.fetchone()

                if question_row:
                    question_id = question_row[0]
                    await cursor.execute("DELETE FROM answers WHERE question_id = ?", (question_id,))

                    correct_answer = random.randint(1, 4)
                    for i in range(1, 5):
                        await cursor.execute("""
                            INSERT INTO answers (question_id, answer_text, is_correct)
                            VALUES (?, ?, ?)
                        """, (question_id, f"Вариант {i}", 1 if i == correct_answer else 0))

        await conn.commit()


async def update_quiz_time(quiz_id, new_time):
    async with db_manager.get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
        "UPDATE quiz_schedule SET start_time = ? WHERE id = ?", (new_time, quiz_id))


@router.message(F.text == "🎓 Квизы")
async def send_quiz(message: Message, state: FSMContext):
    async with db_manager.get_connection() as conn:
        cursor = await conn.cursor()
        quizzes = await cursor.execute("SELECT id, quiz_name, start_time, location FROM quiz_schedule ORDER BY start_time ASC")
        quizzes = await cursor.fetchall()

        current_time = datetime.now().strftime("%H:%M")
        selected_quiz = next(
            (q for q in quizzes if is_within_range(current_time, q[2])), None)

        if selected_quiz:
            await message.answer("Введите кодовое слово:")
            await state.set_state(QuizStates.waiting_code)
            await state.update_data(quiz_id=selected_quiz[0])
        else:
            upcoming = next((q for q in quizzes if q[2] > current_time), None)
            if upcoming:
                await message.answer(f"Ближайший квиз: {upcoming[1]} в {upcoming[2]} ({upcoming[3]})")
            else:
                await message.answer("На сегодня квизов больше нет.")


def is_within_range(current_time_str, target_time_str, delta_minutes=10):
    current_dt = datetime.strptime(current_time_str, "%H:%M")
    target_dt = datetime.strptime(target_time_str, "%H:%M")
    diff = (current_dt - target_dt).total_seconds() / 60.0
    return 0 <= diff <= delta_minutes


@router.message(QuizStates.waiting_code)
async def process_quiz_code(message: Message, state: FSMContext):
    data = await state.get_data()
    quiz_id = data['quiz_id']
    user_input = message.text.lower().strip()
    valid_words = {"сосиска": 1, "колбаса": 2, "1": 3, "2": 4, "3": 5}

    if user_input in valid_words and valid_words[user_input] == quiz_id:
        await start_quiz(message, quiz_id)
    else:
        await message.answer("❌ Неверное кодовое слово.")

    await state.clear()


async def start_quiz(message: Message, quiz_id: int):
    user = message.from_user.username
    if await is_finished_quiz(user, quiz_id):
        await message.answer("Вы уже участвовали в этом квизе.")
        return

    async with db_manager.get_connection() as conn:
        cursor = await conn.cursor()
        question = await cursor.execute("SELECT id FROM questions WHERE quiz_id = ? ORDER BY id ASC LIMIT 1", (quiz_id,))
        question = await question.fetchone()

        if question:
            await send_question(message.chat.id, user, question[0], quiz_id)


async def send_question(chat_id: int, user: str, question_id: int, quiz_id: int):
    async with db_manager.get_connection() as conn:
        cursor = await conn.cursor()
        answers = await cursor.execute("SELECT id, answer_text FROM answers WHERE question_id = ? ORDER BY id ASC", (question_id,))
        answers = await answers.fetchall()

        letters = ["А", "Б", "В", "Г"]
        markup = InlineKeyboardMarkup(row_width=1)

        for idx, (ans_id, ans_text) in enumerate(answers):
            letter = letters[idx] if idx < len(letters) else ans_text
            markup.add(InlineKeyboardButton(
                text=letter,
                callback_data=f"answer:{question_id}:{ans_id}:{user}:{quiz_id}"
            ))

        await bot.send_message(chat_id, f"❔ Вопрос {question_id}", reply_markup=markup)


@router.callback_query(F.data.startswith("answer:"))
async def check_answer(callback: CallbackQuery):
    await callback.answer()
    data = callback.data.split(":")
    question_id, answer_id, user, quiz_id = int(
        data[1]), int(data[2]), data[3], int(data[4])

    async with db_manager.get_connection() as conn:
        cursor = await conn.cursor()

        # Проверка правильности ответа
        is_correct = await cursor.execute("SELECT is_correct FROM answers WHERE id = ?", (answer_id,))
        is_correct = (await is_correct.fetchone())[0]

        if is_correct:
            await update_quize_points(user, quiz_id)

        # Получение следующего вопроса
        next_question = await cursor.execute("""
            SELECT id FROM questions 
            WHERE quiz_id = ? AND id > ? 
            ORDER BY id ASC LIMIT 1
        """, (quiz_id, question_id))
        next_question = await next_question.fetchone()

        if next_question:
            await send_question(callback.message.chat.id, user, next_question[0], quiz_id)
        else:
            points = await check_quiz_points(user, quiz_id)
            await callback.message.answer(f"Квиз завершён! Ваши баллы: {points}")
