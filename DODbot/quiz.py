from bot import bot
import sqlite3
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboard import main_keyboard
from users import update_quize_points, is_finished_quiz, check_quiz_points
from datetime import datetime
import random


def create_quiz_table():
    conn = sqlite3.connect("quiz.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quiz_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quiz_name TEXT NOT NULL,
        start_time TEXT CHECK (LENGTH(start_time) = 5 AND start_time LIKE '__:__'), -- Ограничение формата HH:MM
        is_started INTEGER DEFAULT 0
    )
    """)
    cursor.execute("""
    INSERT OR IGNORE INTO quize_schedule (quiz_name, start_time) VALUES 
        ("Квиз 1", "11:00"),
        ("Квиз 2", "12:00"),
        ("Квиз 3", "13:00"),
        ("Квиз 4", "14:00"),
        ("Квиз 5", "15:00");
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quiz_id INTEGER NOT NULL,
        FOREIGN KEY (quiz_id) REFERENCES quizzes(id)
    )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS answers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER NOT NULL,
        answer_text TEXT NOT NULL,
        is_correct INTEGER DEFAULT 0,
        FOREIGN KEY(question_id) REFERENCES questions(id)
    )
    """)

    cursor.execute("SELECT id FROM quizzes")
    quiz_ids = [row[0] for row in cursor.fetchall()]

    for quiz_id in quiz_ids:
        for _ in range(25):
            cursor.execute(
                "INSERT INTO questions (quiz_id) VALUES (?)", (quiz_id,))
            question_id = cursor.lastrowid

            correct_answer = random.randint(1, 4)
            for i in range(1, 5):
                cursor.execute("INSERT INTO answers (question_id, answer_text, is_correct) VALUES (?, ?, ?)",
                               (question_id, f"Вариант {i}", 1 if i == correct_answer else 0))

    conn.commit()
    conn.close()


create_quiz_table()


def get_db_connection():
    return sqlite3.connect("quiz.db", check_same_thread=False)


def is_within_range(current_time_str, target_time_str, delta_minutes=10):
    current_dt = datetime.strptime(current_time_str, "%H:%M")
    target_dt = datetime.strptime(target_time_str, "%H:%M")
    diff = (current_dt - target_dt).total_seconds() / 60.0
    if diff < 0:
        return False
    return diff <= delta_minutes

@bot.message_handler(func=lambda message: message.text == "🎓 Квизы")
def send_quiz(m):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, name, time, location FROM quizzes ORDER BY time ASC")
    quizzes = cur.fetchall()

    current_time = datetime.now().strftime("%H:%M")
    selected_quiz = None

    for quiz_id, name, time, location in quizzes:
        if is_within_range(current_time, time):
            selected_quiz = (quiz_id, name, time, location)
            break

    if selected_quiz:
        quiz_id, quiz_name, quiz_time, location = selected_quiz
        bot.send_message(m.chat.id, "Введите кодовое слово:")
        bot.register_next_step_handler(
            m, lambda message: process_quiz_start(message, quiz_id))
    else:
        upcoming = next(
            (quiz for quiz in quizzes if quiz[2] > current_time), None)
        if upcoming:
            bot.send_message(
                m.chat.id, f"Ближайший квиз: {upcoming[1]} в {upcoming[2]} ({upcoming[3]})")
        else:
            bot.send_message(m.chat.id, "На сегодня квизов больше нет.")

    conn.close()


def process_quiz_start(message, quiz_id):
    user_input = message.text.lower().strip()
    valid_words = ["сосиска", "колбаса", "1", "2", "3"]

    if user_input in valid_words:
        start_quiz(message, quiz_id)
    else:
        bot.send_message(message.chat.id, "❌ Неверное кодовое слово.")

def start_quiz(message, quiz_id):
    user = message.from_user.username
    if is_finished_quiz(user, quiz_id):
        bot.send_message(message.chat.id, "Вы уже участвовали в этом квизе.")
        return

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, text FROM questions WHERE quiz_id = ? ORDER BY id ASC LIMIT 1", (quiz_id,))
    question = cur.fetchone()

    if question:
        question_id, question_text = question
        send_question(message.chat.id, user, question_id, question_text)

    conn.close()

def send_question(chat_id, user, question_id, question_text):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, text FROM answers WHERE question_id = ?", (question_id,))
    answers = cur.fetchall()

    markup = InlineKeyboardMarkup(row_width=1)
    for ans_id, ans_text in answers:
        markup.add(InlineKeyboardButton(
            ans_text, callback_data=f"answer:{question_id}:{ans_id}:{user}"))

    bot.send_message(chat_id, question_text, reply_markup=markup)
    conn.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith("answer:"))
def check_answer(call):
    bot.answer_callback_query(call.id)
    _, question_id, answer_id, user = call.data.split(":")
    question_id, answer_id = int(question_id), int(answer_id)

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT is_correct FROM answers WHERE id = ?", (answer_id,))
    result = cur.fetchone()

    if result and result[0] == 1:
        update_quize_points(user, question_id)

    cur.execute("""
        SELECT id, text FROM questions 
        WHERE id > ? ORDER BY id ASC LIMIT 1
    """, (question_id,))
    next_question = cur.fetchone()

    if next_question:
        next_question_id, next_question_text = next_question
        send_question(call.message.chat.id, user,
                      next_question_id, next_question_text)
    else:
        bot.send_message(
            call.message.chat.id, f"Квиз завершён! Ваши баллы: {check_quiz_points(user)}", reply_markup=main_keyboard())

    conn.close()
