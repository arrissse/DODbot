from bot import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from users import update_quize_points, is_finished_quiz, check_quiz_points
from datetime import datetime, time as dt_time
import random
import logging
from database import db_manager
from keyboard import main_keyboard

# Настройка логгера
logger = logging.getLogger(__name__)

# Константы
LETTERS = ["А", "Б", "В", "Г"]
CODE_WORDS = {
    1: "сосиска",
    2: "колбаса",
    3: "1",
    4: "2",
    5: "3"
}


def create_quiz_table():
    """Инициализация структуры БД для квизов"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Создание таблиц
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS quiz_schedule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quiz_name TEXT NOT NULL,
                    start_time TEXT CHECK(length(start_time) = 5 AND start_time GLOB '[0-9][0-9]:[0-9][0-9]'),
                    location TEXT NOT NULL,
                    is_started INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quiz_id INTEGER NOT NULL,
                    question_number INTEGER NOT NULL,
                    text TEXT DEFAULT 'Вопрос без текста',
                    UNIQUE(quiz_id, question_number),
                    FOREIGN KEY (quiz_id) REFERENCES quiz_schedule(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id INTEGER NOT NULL,
                    answer_text TEXT NOT NULL,
                    is_correct INTEGER DEFAULT 0 CHECK(is_correct IN (0, 1)),
                    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
                );
            """)

            # Инициализация тестовых данных
            cursor.execute("""
                INSERT OR IGNORE INTO quiz_schedule (quiz_name, start_time, location) VALUES
                    ("Квиз 1", "11:00", "113 ГК"),
                    ("Квиз 2", "12:00", "4.16 Цифра"),
                    ("Квиз 3", "13:00", "423 ГК"),
                    ("Квиз 4", "14:00", "4.6 Арктика"),
                    ("Квиз 5", "15:00", "305 ЛК");
            """)

            # Генерация вопросов и ответов
            cursor.execute("SELECT id FROM quiz_schedule")
            for quiz_id, in cursor.fetchall():
                generate_quiz_questions(conn, quiz_id)

            
            logger.info("Таблицы квизов успешно инициализированы")

    except Exception as e:
        logger.error(f"Ошибка инициализации квизов: {e}")
        raise


def generate_quiz_questions(conn, quiz_id):
    """Генерация вопросов и ответов для квиза"""
    try:
        cursor = conn.cursor()

        # Создание 25 вопросов
        for q_num in range(1, 26):
            cursor.execute("""
                INSERT OR IGNORE INTO questions (quiz_id, question_number, text)
                VALUES (?, ?, ?)
            """, (quiz_id, q_num, f"Вопрос {q_num} для квиза {quiz_id}"))

            # Получение ID созданного вопроса
            cursor.execute("""
                SELECT id FROM questions
                WHERE quiz_id = ? AND question_number = ?
            """, (quiz_id, q_num))

            if question_row := cursor.fetchone():
                question_id = question_row[0]
                # Удаление старых ответов
                cursor.execute(
                    "DELETE FROM answers WHERE question_id = ?", (question_id,))

                # Генерация новых ответов
                correct_answer = random.randint(1, 4)
                for ans_num in range(1, 5):
                    cursor.execute("""
                        INSERT INTO answers (question_id, answer_text, is_correct)
                        VALUES (?, ?, ?)
                    """, (question_id, f"Вариант {ans_num}", 1 if ans_num == correct_answer else 0))

        logger.debug(f"Сгенерированы вопросы для квиза {quiz_id}")

    except Exception as e:
        logger.error(f"Ошибка генерации вопросов: {e}")
        raise


def update_quiz_time(quiz_id: int, new_time: str):
    """Обновление времени начала квиза"""
    try:
        # Валидация формата времени
        datetime.strptime(new_time, "%H:%M")

        with db_manager.get_connection() as conn:
            conn.execute(
                "UPDATE quiz_schedule SET start_time = ? WHERE id = ?",
                (new_time, quiz_id))
            
            logger.info(f"Обновлено время квиза {quiz_id} на {new_time}")

    except ValueError:
         logger.error(f"Некорректный формат времени: {new_time}")
         raise
    except Exception as e:
        logger.error(f"Ошибка обновления времени: {e}")
        raise


def is_within_range(current_time_str: str, target_time_str: str, delta_minutes=10) -> bool:
    """Проверка попадания времени в допустимый диапазон"""
    try:
        current = datetime.strptime(current_time_str, "%H:%M").time()
        target = datetime.strptime(target_time_str, "%H:%M").time()

        current_sec = current.hour * 3600 + current.minute * 60
        target_sec = target.hour * 3600 + target.minute * 60

        return 0 <= (current_sec - target_sec) <= delta_minutes * 60

    except ValueError as e:
        logger.error(f"Ошибка парсинга времени: {e}")
        return False


@bot.message_handler(func=lambda m: m.text == "🎓 Квизы")
def handle_quiz_command(message):
    """Обработчик команды 'Квизы'"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, quiz_name, start_time, location 
                FROM quiz_schedule 
                ORDER BY start_time ASC
            """)

            current_time = datetime.now().strftime("%H:%M")
            quizzes = cursor.fetchall()

            # Поиск активного квиза
            active_quiz = next(
                (q for q in quizzes if is_within_range(current_time, q[2])),
                None
            )

            if active_quiz:
                quiz_id, name, time, location = active_quiz
                bot.send_message(
                    message.chat.id,
                    f"🕒 Сейчас проходит {name} ({time})!\n"
                    f"📍 Место: {location}\n"
                    "🔢 Введите кодовое слово:"
                )
                bot.register_next_step_handler(
                    message,
                    lambda m: process_quiz_start(m, quiz_id)
                )
            else:
                # Поиск ближайшего квиза
                upcoming = next(
                    (q for q in quizzes if q[2] > current_time),
                    None
                )

                if upcoming:
                    msg = (f"⏳ Ближайший квиз:\n"
                           f"📌 {upcoming[1]}\n"
                           f"🕒 {upcoming[2]}\n"
                           f"📍 {upcoming[3]}")
                else:
                    msg = "📭 На сегодня квизов больше нет."

                bot.send_message(message.chat.id, msg)

    except Exception as e:
        logger.error(f"Ошибка обработки команды квиза: {e}")
        bot.send_message(
            message.chat.id, "⚠️ Произошла ошибка, попробуйте позже")


def process_quiz_start(message, quiz_id: int):
    """Обработка кодового слова"""
    try:
        user_input = message.text.strip().lower()
        expected_word = CODE_WORDS.get(quiz_id)

        if user_input == expected_word:
            start_quiz(message, quiz_id)
        else:
            bot.send_message(message.chat.id, "❌ Неверное кодовое слово")

    except Exception as e:
        logger.error(f"Ошибка старта квиза: {e}")
        bot.send_message(message.chat.id, "⚠️ Ошибка запуска квиза")


def start_quiz(message, quiz_id: int):
    """Запуск квиза для пользователя"""
    try:
        user = message.from_user.username
        if not user:
            raise ValueError("Не удалось получить username")

        if is_finished_quiz(user, quiz_id):
            bot.send_message(message.chat.id, "✋ Вы уже прошли этот квиз")
            return

        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM questions 
                WHERE quiz_id = ? 
                ORDER BY question_number ASC 
                LIMIT 1
            """, (quiz_id,))

            if first_question := cursor.fetchone():
                send_question(message.chat.id, user,
                              first_question[0], quiz_id)
            else:
                bot.send_message(
                    message.chat.id, "⚠️ В этом квизе пока нет вопросов")

    except Exception as e:
        logger.error(f"Ошибка запуска квиза: {e}")
        bot.send_message(message.chat.id, "⚠️ Ошибка запуска квиза")


def send_question(chat_id: int, user: str, question_id: int, quiz_id: int):
    """Отправка вопроса пользователю"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Получение вариантов ответов
            cursor.execute("""
                SELECT id, answer_text 
                FROM answers 
                WHERE question_id = ? 
                ORDER BY id ASC
            """, (question_id,))
            answers = cursor.fetchall()

            # Создание клавиатуры
            markup = InlineKeyboardMarkup(row_width=2)
            for idx, (ans_id, text) in enumerate(answers):
                markup.add(InlineKeyboardButton(
                    text=f"{LETTERS[idx]} {text}",
                    callback_data=f"answer_{question_id}_{ans_id}_{user}_{quiz_id}"
                ))

            # Отправка вопроса
            bot.send_message(
                chat_id,
                f"❓ Вопрос #{question_id}",
                reply_markup=markup
            )

    except Exception as e:
        logger.error(f"Ошибка отправки вопроса: {e}")
        bot.send_message(chat_id, "⚠️ Ошибка загрузки вопроса")


@bot.callback_query_handler(func=lambda call: call.data.startswith("answer_"))
def handle_answer(call):
    """Обработка ответа пользователя"""
    try:
        bot.answer_callback_query(call.id)
        parts = call.data.split('_')
        if len(parts) != 5:
            raise ValueError("Неверный формат callback данных")

        _, question_id, answer_id, user, quiz_id = parts
        question_id = int(question_id)
        answer_id = int(answer_id)
        quiz_id = int(quiz_id)

        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Проверка правильности ответа
            cursor.execute("""
                SELECT is_correct 
                FROM answers 
                WHERE id = ?
            """, (answer_id,))

            if (result := cursor.fetchone()) and result[0] == 1:
                update_quize_points(user, quiz_id, 1)
                logger.info(f"Пользователь {user} дал правильный ответ")

            # Поиск следующего вопроса
            cursor.execute("""
                SELECT id FROM questions 
                WHERE quiz_id = ? AND id > ? 
                ORDER BY id ASC 
                LIMIT 1
            """, (quiz_id, question_id))

            if next_question := cursor.fetchone():
                send_question(call.message.chat.id, user,
                              next_question[0], quiz_id)
            else:
                score = check_quiz_points(user, quiz_id)
                bot.send_message(
                    call.message.chat.id,
                    f"🏁 Квиз завершен!\n"
                    f"🎉 Ваш результат: {score} баллов",
                    reply_markup=main_keyboard()
                )
                logger.info(
                    f"Пользователь {user} завершил квиз {quiz_id} с результатом {score}")

    except Exception as e:
        logger.error(f"Ошибка обработки ответа: {e}")
        bot.send_message(call.message.chat.id, "⚠️ Ошибка обработки ответа")
