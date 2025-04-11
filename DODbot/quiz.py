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

    # Создание таблицы расписания квизов
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quiz_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quiz_name TEXT NOT NULL,
        start_time TEXT CHECK (LENGTH(start_time) = 5 AND start_time LIKE '__:__'), -- Ограничение формата HH:MM
        location TEXT NOT NULL,
        is_started INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    INSERT OR IGNORE INTO quiz_schedule (quiz_name, start_time, location) VALUES 
        ("Квиз 1", "11:00", "113 ГК"),
        ("Квиз 2", "12:00", "4.16 Цифра"),
        ("Квиз 3", "13:00", "423 ГК"),
        ("Квиз 4", "14:00", "4.6 Арктика"),
        ("Квиз 5", "15:00", "305 ЛК");
    """)

    # Создание таблицы вопросов с полем question_number и уникальным ограничением для (quiz_id, question_number)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER NOT NULL,
            question_number INTEGER NOT NULL,
            text TEXT DEFAULT 'Вопрос без текста', 
            UNIQUE(quiz_id, question_number),
            FOREIGN KEY (quiz_id) REFERENCES quiz_schedule(id)
        )
    """)

    # Создание таблицы вариантов ответов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS answers(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            answer_text TEXT NOT NULL,
            is_correct INTEGER DEFAULT 0,
            FOREIGN KEY(question_id) REFERENCES questions(id)
        )
    """)

    cursor.execute("SELECT id FROM quiz_schedule")
    quiz_ids = [row[0] for row in cursor.fetchall()]

    # Для каждого квиза вставляем ровно 25 вопросов, используя question_number для уникальности
    for quiz_id in quiz_ids:
        for question_number in range(1, 26):
            # Пытаемся вставить вопрос; если такой уже есть – пропускаем его (INSERT OR IGNORE)
            cursor.execute("""
                INSERT OR IGNORE INTO questions (quiz_id, question_number, text)
                VALUES (?, ?, ?)
            """, (quiz_id, question_number, f"Вопрос {question_number} для квиза {quiz_id}"))
            # Получаем id вопроса только что вставленной или уже существующей записи
            cursor.execute("""
                SELECT id FROM questions WHERE quiz_id = ? AND question_number = ?
            """, (quiz_id, question_number))
            question_row = cursor.fetchone()
            if question_row:
                question_id = question_row[0]
                # Удаляем (или обновляем) варианты ответов для данного вопроса, если они уже существуют
                cursor.execute(
                    "DELETE FROM answers WHERE question_id = ?", (question_id,))

                correct_answer = random.randint(1, 4)
                for i in range(1, 5):
                    cursor.execute("""
                        INSERT INTO answers (question_id, answer_text, is_correct)
                        VALUES (?, ?, ?)
                    """, (question_id, f"Вариант {i}", 1 if i == correct_answer else 0))
            else:
                print(
                    f"Не удалось получить вопрос для quiz_id {quiz_id} и question_number {question_number}")

    conn.commit()
    conn.close()


def get_db_connection():
    return sqlite3.connect("quiz.db", check_same_thread=False)


def update_quiz_time(quiz_id, new_time):
    conn = sqlite3.connect("quiz.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE quiz_schedule SET start_time = ? WHERE id = ?", (new_time, quiz_id))

    conn.commit()
    conn.close()



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

    cur.execute("SELECT id, quiz_name, start_time, location FROM quiz_schedule ORDER BY start_time ASC")
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
  try:
    user_input = message.text.lower().strip()
    valid_words = ["сосиска", "колбаса", "1", "2", "3"]

    if user_input in valid_words:
        if user_input == "сосиска" and quiz_id == 1:
            start_quiz(message, 1)
        elif user_input == "колбаса" and quiz_id == 2:
            start_quiz(message, 2)
        elif user_input == "1" and quiz_id == 3:
            start_quiz(message, 3)
        elif user_input == "2" and quiz_id == 4:
            start_quiz(message, 4)
        elif user_input == "3" and quiz_id == 5:
            start_quiz(message, 5)
        else:
            bot.send_message(message.chat.id, "❌ Неверное кодовое слово.")
    else:
        bot.send_message(message.chat.id, "❌ Неверное кодовое слово.")
  except Exception as e:
      bot.send_message(message.chat.id, e)

def start_quiz(message, quiz_id):
    user = message.from_user.username
    if is_finished_quiz(user, quiz_id):
        bot.send_message(message.chat.id, "Вы уже участвовали в этом квизе.")
        return

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id FROM questions WHERE quiz_id = ? ORDER BY id ASC LIMIT 1", (quiz_id,))
    question = cur.fetchone()


    if question:
        question_id = question[0]
        send_question(message.chat.id, user, question_id, quiz_id)

    conn.close()


def send_question(chat_id, user, question_id, quize_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, answer_text FROM answers WHERE question_id = ?", (question_id,))
    answers = cur.fetchall()

    markup = InlineKeyboardMarkup(row_width=1)
    for ans_id, ans_text in answers:
        markup.add(InlineKeyboardButton(
            ans_text, callback_data=f"answer:{question_id}:{ans_id}:{user}:{quize_id}"))

    bot.send_message(chat_id, f"❔ Вопрос {question_id}", reply_markup=markup)
    conn.close()


@bot.callback_query_handler(func=lambda call: call.data.startswith("answer:"))
def check_answer(call):
  try:
    bot.answer_callback_query(call.id)
    _, question_id, answer_id, user, quiz_id = call.data.split(":")
    question_id, answer_id = int(question_id), int(answer_id)

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT is_correct FROM answers WHERE id = ?", (answer_id,))
    result = cur.fetchone()

    if result and result[0] == 1:
        update_quize_points(user, quiz_id)
    cur.execute("SELECT quiz_id FROM questions WHERE id = ?", (question_id,))
    quiz_id = cur.fetchone()[0]

    cur.execute("""
    SELECT id FROM questions 
    WHERE quiz_id = ? AND id > ? ORDER BY id ASC LIMIT 1
    """, (quiz_id, question_id))


    next_question = cur.fetchone()

    if next_question:
        next_question_id = next_question[0]
        send_question(call.message.chat.id, user,
                      next_question_id, quiz_id)
    else:
        bot.send_message(
            call.message.chat.id, f"Квиз завершён! Ваши баллы: {check_quiz_points(user)}", reply_markup=main_keyboard())

    conn.close()
  except Exception as e:
      bot.send_message(call.message.chat.id, e)

