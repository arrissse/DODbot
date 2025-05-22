import logging
import re
from datetime import datetime

from aiogram import F
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from docx import Document

from bot import bot, router
from constants import DEFAULT_QUIZEZ, DOCX_PATH, VALID_WORDS
from src.database.base import db_manager
from src.database.users import (check_quiz_points, is_finished_quiz,
                                update_quize_points)


class QuizStates(StatesGroup):
    """Finite‐state machine states for quiz flow."""
    waiting_code = State()


def normalize_whitespace(string):
    """
    Нормализация пробельных символов в строке.

    Args:
        string: Исходная строка для обработки

    Returns:
        string: Строка с удаленными начальными/конечными пробелами
            и одиночными пробелами между словами
    """
    return " ".join(string.strip().split())

def parse_quiz_document(docx_path):
    """
    Парсит .docx-файл с квизами и возвращает список словарей-описаний:
      [
        {
          "quiz_number": int,      # номер квиза, например 1, 2, 3 …
          "quiz_name": str,        # заголовок квиза (без «Квиз N:»)
          "questions": [
            {
              "number": int,       # номер вопроса
              "text": str,         # текст вопроса
              "answers": [
                {"letter": "А", "text": "...", "is_correct": True/False},
                {"letter": "Б", "text": "...", "is_correct": True/False},
                …
              ]
            },
            …
          ]
        },
        …
      ]

    Предполагается, что внутри .docx:
    - Заголовок квиза будет в формате “Квиз <number>: «<название>» ...”.
    - Вопросы и варианты ответов могут находиться в одном абзаце:
      “14. Текст вопроса? А. Вариант А В. Вариант В Г. Вариант Г”.
    - Правильный ответ в .docx выделен жирным (run.bold == True).
    """
    doc = Document(docx_path)
    quizzes = []

    quiz_header_re = re.compile(
        r"^Квиз\s+(\d+)\s*[:：]\s*«?(.*?)»?(?:\s*\(.*\))?$",
        re.IGNORECASE
    )
    question_re = re.compile(r"^(\d+)\.\s*(.+)$")
    option_re = re.compile(r"^([А-Г])\.\s*(.+)$")

    current_quiz = None
    current_question = None

    for para in doc.paragraphs:
        line = normalize_whitespace(para.text)
        if not line:
            continue

        m_quiz = quiz_header_re.match(line)
        if m_quiz:
            quiz_number = int(m_quiz.group(1))
            quiz_name = m_quiz.group(2).strip()

            current_quiz = {
                "quiz_number": quiz_number,
                "quiz_name": quiz_name,
                "questions": []
            }
            quizzes.append(current_quiz)
            current_question = None
            continue

        if current_quiz is None:
            continue

        m_q = question_re.match(line)
        if m_q:
            q_number = int(m_q.group(1))
            q_text = m_q.group(2).strip()
            current_question = {
                "number": q_number,
                "text": q_text,
                "answers": []
            }
            current_quiz["questions"].append(current_question)
            continue

        m_opt = option_re.match(line)
        if m_opt and current_question is not None:
            letter = m_opt.group(1)
            ans_text = m_opt.group(2).strip()

            is_bold = False
            for run in para.runs:
                text_run = normalize_whitespace(run.text)
                if run.bold and text_run.startswith(letter + "."):
                    is_bold = True
                    break

            current_question["answers"].append({
                "letter": letter,
                "text": ans_text,
                "is_correct": is_bold
            })
            continue

        continue

    return quizzes


async def create_quiz_table():
    """Ensure quiz_schedule, questions, and answers tables exist and are populated.

    - Creates `quiz_schedule` with default quiz entries (time, location).
    - Creates `questions` for each quiz, 25 questions per quiz, with placeholder text.
    - Creates `answers` table and populates four options per question, one correct
      at random.
    """
    async with db_manager.get_connection() as conn:
        cursor = await conn.cursor()

        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_name TEXT NOT NULL,
                start_time TEXT CHECK (LENGTH(start_time) = 5 AND start_time LIKE '__:__'),
                location TEXT NOT NULL,
                is_started INTEGER DEFAULT 0
            )
        """)

        for quiz_name, start_time, location in DEFAULT_QUIZEZ:
            await cursor.execute(
                "INSERT OR IGNORE INTO quiz_schedule (quiz_name, start_time, location) VALUES (?, ?, ?)",
                (quiz_name, start_time, location)
            )

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

        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS answers(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                answer_text TEXT NOT NULL,
                is_correct INTEGER DEFAULT 0,
                FOREIGN KEY(question_id) REFERENCES questions(id)
            )
        """)

        quizzes_data = parse_quiz_document(DOCX_PATH)

        for quiz in quizzes_data:
            quiz_id = quiz["quiz_number"]

            row = await (await cursor.execute(
                "SELECT id FROM quiz_schedule WHERE id = ?", (quiz_id,)
            )).fetchone()

            for q in quiz["questions"]:
                qnum = q["number"]
                qtext = q["text"]

                await cursor.execute("""
                    INSERT INTO questions (quiz_id, question_number, text)
                    VALUES (?, ?, ?)
                """, (quiz_id, qnum, qtext))

                question_id = (await (await cursor.execute(
                    "SELECT last_insert_rowid()"
                )).fetchone())[0]

                for ans in q["answers"]:
                    await cursor.execute("""
                        INSERT INTO answers (question_id, answer_text, is_correct)
                        VALUES (?, ?, ?)
                    """, (question_id, ans["text"], int(ans["is_correct"])))


async def update_quiz_time(quiz_id, new_time):
    """Change the start_time field for a quiz.

    Args:
        quiz_id: The `id` in `quiz_schedule` to update.
        new_time: New time as `"HH:MM"`; must satisfy the table’s CHECK constraint.
    """
    async with db_manager.get_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            "UPDATE quiz_schedule SET start_time = ? WHERE id = ?", (new_time, quiz_id))


@router.message(F.text == "🎓 Квизы")
async def send_quiz(message, state):
    """Handler for “🎓 Квизы”: choose the current or next quiz and prompt for code.

    - If a quiz is already live (within 10 min after its start_time), ask
      the user to enter a code word and set FSM to `waiting_code`.
    - Otherwise, announce the next quiz or say “no more today.”

    Args:
        message (Message):
            The incoming message object from the user,
            containing:
              - `message.text == "🎓 Квизы"`
              - chat and user context for replying.
        state (FSMContext):
            The finite-state machine context for the current chat/user,
            used to set or update the user'str quiz state and store
            temporary data (e.g., `quiz_id`).
    """
    async with db_manager.get_connection() as conn:
        cursor = await conn.cursor()
        quizzes = await cursor.execute(
            "SELECT id, quiz_name, start_time, location "
            "FROM quiz_schedule ORDER BY start_time ASC"
        )
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
    """Return True if current_time is within [target_time .. target_time + delta_minutes].

    Args:
        current_time_str: `"HH:MM"` current time.
        target_time_str: `"HH:MM"` quiz start time.
        delta_minutes: Window size in minutes after start.

    Returns:
        True if 0 <= (current - target) ≤ delta_minutes, else False.
    """

    current_dt = datetime.strptime(current_time_str, "%H:%M")
    target_dt = datetime.strptime(target_time_str, "%H:%M")
    diff = (current_dt - target_dt).total_seconds() / 60.0
    return 0 <= diff <= delta_minutes


@router.message(QuizStates.waiting_code)
async def process_quiz_code(message, state):
    """Validate the user’s code word and begin quiz if correct.

    - Expects `message.text` to match one of the preset words
      and correspond to that quiz’s `id`.
    - If valid, calls `start_quiz`; otherwise replies “❌ Неверное кодовое слово.”
    - Clears FSM state afterward.

    Args:
        message (Message): The code word message from the user.
        state (FSMContext): FSM context containing `quiz_id`.
    """
    data = await state.get_data()
    quiz_id = data['quiz_id']
    user_input = message.text.lower().strip()

    if user_input in VALID_WORDS and VALID_WORDS[user_input] == quiz_id:
        await start_quiz(message, quiz_id)
    else:
        await message.answer("❌ Неверное кодовое слово.")

    await state.clear()


async def start_quiz(message, quiz_id):
    """Fetch the first unanswered question for `quiz_id` and send it.

    Args:
        message: The original trigger message (to get chat & user).
        quiz_id: ID of the quiz to start.
    """
    user = message.from_user.username

    if await is_finished_quiz(user, quiz_id):
        await message.answer("Вы уже участвовали в этом квизе.")
        return

    async with db_manager.get_connection() as conn:
        cursor = await conn.cursor()
        question = await cursor.execute(
            "SELECT id FROM questions WHERE quiz_id = ? ORDER BY id ASC LIMIT 1",
            (quiz_id,)
        )
        question = await question.fetchone()
        question_number = await cursor.execute(
            "SELECT question_number FROM questions WHERE quiz_id = ? ORDER BY id ASC LIMIT 1",
            (quiz_id,))
        question_number = await question_number.fetchone()
        if question:
            await send_question(message.chat.id, user, question[0], question_number[0], quiz_id)


async def send_question(chat_id, user, question_id, question_number, quiz_id):
    """
    Retrieve all answers for a question and send buttons.

    Args:
        chat_id: ID чата для отправки вопроса
        user: Имя пользователя
        question_id: ID вопроса
        question_number: Номер вопроса
        quiz_id: ID квиза
    """
    async with db_manager.get_connection() as conn:
        cursor = await conn.cursor()
        answers = await cursor.execute(
            "SELECT id, answer_text FROM answers "
            "WHERE question_id = ? ORDER BY id ASC", (question_id,)
        )
        answers = await answers.fetchall()
        letters = ["А", "Б", "В", "Г"]
        keyboard = []
        for idx, (ans_id, ans_text) in enumerate(answers):
            letter = letters[idx] if idx < len(letters) else ans_text
            button = InlineKeyboardButton(
                text=letter,
                callback_data=f"answer:{question_id}:{ans_id}:{user}:{quiz_id}"
            )
            keyboard.append([button])

        markup = InlineKeyboardMarkup(inline_keyboard=keyboard, row_width=1)
        await bot.send_message(chat_id, f"❔ Вопрос {question_number}", reply_markup=markup)


@router.callback_query(F.data.startswith("answer:"))
async def check_answer(callback):
    """Handle answer-button clicks, award points, and advance or finish.

    Args:
        callback: The callback query with data "answer:...".
    """
    try:
        await callback.answer()
        data = callback.data.split(":")
        question_id, answer_id, user, quiz_id = int(
            data[1]), int(data[2]), data[3], int(data[4])

        async with db_manager.get_connection() as conn:
            cursor = await conn.cursor()

            is_correct_row = await cursor.execute(
                "SELECT is_correct FROM answers WHERE id = ?", (answer_id,))
            is_correct = (await is_correct_row.fetchone())[0]

            if is_correct:
                await update_quize_points(user, quiz_id)

            current_qnum_row = await cursor.execute(
                "SELECT question_number FROM questions WHERE id = ?", (question_id,))
            current_qnum = (await current_qnum_row.fetchone())[0]

            next_question_row = await cursor.execute("""
                SELECT id FROM questions
                WHERE quiz_id = ? AND question_number > ?
                ORDER BY question_number ASC LIMIT 1
            """, (quiz_id, current_qnum))
            next_question = await next_question_row.fetchone()

            if next_question:
                next_question_num = await cursor.execute("""
                    SELECT question_number FROM questions
                    WHERE quiz_id = ? AND id = ?
                    ORDER BY id ASC LIMIT 1
                """, (quiz_id, next_question[0]))
                next_question_num = await next_question_num.fetchone()
                await send_question(callback.message.chat.id, user, next_question[0], next_question_num[0], quiz_id)
            else:
                points = await check_quiz_points(user, quiz_id)
                await callback.message.answer(
                    f"Квиз завершён! Ваши баллы: {points}")
    except Exception as err:
        logging.exception(err)
