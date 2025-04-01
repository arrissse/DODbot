from bot import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboard import main_keyboard
from users import update_quize_points, is_finished_quiz, check_quiz_points
from datetime import datetime

def is_within_range(current_time_str, target_time_str, delta_minutes=10):
    current_dt = datetime.strptime(current_time_str, "%H:%M")
    target_dt = datetime.strptime(target_time_str, "%H:%M")
    diff = (current_dt - target_dt).total_seconds() / 60.0
    if diff < 0:
        return False
    return diff <= delta_minutes

quiz_schedule = {
    "11:00": ("Квиз 1: География", "Аудитория 101", "quiz1"),
    "12:00": ("Квиз 2: История", "Аудитория 102", "quiz2"),
    "13:00": ("Квиз 3: Наука", "Аудитория 103", "quiz3"),
    "14:00": ("Квиз 4: Литература", "Аудитория 104", "quiz4"),
    "15:00": ("Квиз 5: Спорт", "Аудитория 105", "quiz5")
}

@bot.message_handler(func=lambda message: message.text == "🎓 Квизы")
def send_quiz(m):
    try:
        current_time = datetime.now().strftime("%H:%M")
        selected_quiz = None

        for quiz_time, info in quiz_schedule.items():
            if is_within_range(current_time, quiz_time, delta_minutes=10):
                selected_quiz = (quiz_time, info)
                break
        if selected_quiz:
            quiz_time, (quiz_name, location, quiz_function_name) = selected_quiz
            bot.send_message(m.chat.id, "Введите кодовое слово:")
        else:
            for time, info in quiz_schedule.items():
                upcoming = None
                if time > current_time:
                    upcoming = [time, info]
                    break
            if upcoming:
                n_quiz_time, (n_quiz_name, n_location, n_quiz_function_name) = upcoming
            else:
                next_quiz_time = min(quiz_schedule.keys())
            bot.send_message(m.chat.id, f"Ближайший квиз начнется в {n_quiz_time} в {n_location}")
            return
    except Exception as e:
        bot.send_message(m.chat.id, e)

    def process_message(message):
        message_text = message.text.lower().strip()
        words = ["сосиска", "колбаса", "1", "2", "3"]
        if message_text in words:
            if selected_quiz:
                _, (_, _, quiz_function_name) = selected_quiz
                quiz_func = globals().get(quiz_function_name)
                if quiz_func:
                    quiz_func(message)
                else:
                    bot.send_message(message.chat.id, "Ошибка: функция квиза не найдена.")
            else:
                bot.send_message(message.chat.id, "Нет квиза для запуска.")
        else:
            bot.send_message(message.chat.id, "❌ Неверное кодовое слово.")

    bot.register_next_step_handler(m, process_message)

correct_answers = {
    1: "2",
    2: "3",
    3: "1"
}


# Квиз 1: География
def quiz1(message):
    user = message.from_user.username
    print(user)
    if is_finished_quiz(user, 1):
        bot.send_message(message.chat.id, "Вы уже участвовали в этом квизе.")
        return
    bot.send_message(message.chat.id, "Квиз 1: География")
    bot.send_message(message.chat.id, "Вопрос 1: Какой из этих городов является столицей Франции?")

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("1) Берлин", callback_data=f"select_station:1:{user}"),
        InlineKeyboardButton("2) Париж", callback_data=f"select_station:2:{user}"),
        InlineKeyboardButton("3) Рим", callback_data=f"select_station:3:{user}"),
        InlineKeyboardButton("4) Лондон", callback_data=f"select_station:4:{user}")
    )

    bot.send_message(message.chat.id, "Выберите ответ:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_station:"))
def check_answer_1(call):
    bot.answer_callback_query(call.id)

    parts = call.data.split(":")
    ans = parts[1]
    user = parts[2]
    print(ans, " ", user)
    chat_id = call.message.chat.id
    print(f"{user}, {ans}") 
    if int(ans) == int(correct_answers[1]):
        update_quize_points(user, 1)

    bot.send_message(chat_id, "Вопрос 2: Какой океан является самым большим?")
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
            InlineKeyboardButton("1) Атлантический", callback_data=f"select_ocean:1:{user}"),
            InlineKeyboardButton("2) Индийский", callback_data=f"select_ocean:2:{user}"),
            InlineKeyboardButton("3) Тихий", callback_data=f"select_ocean:3:{user}"),
            InlineKeyboardButton("4) Южный", callback_data=f"select_ocean:4:{user}")
    )
    bot.send_message(chat_id, "Выберите ответ:", reply_markup=markup)     

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_ocean:"))
def check_answer_2(call):
    bot.answer_callback_query(call.id)

    parts = call.data.split(":")
    ans = parts[1]
    user = parts[2]
    chat_id = call.message.chat.id
    print(f"{ans}") 
    if int(ans) == int(correct_answers[2]):
        update_quize_points(user, 1)

    bot.send_message(chat_id, "Вопрос 3: Сосал?")
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
            InlineKeyboardButton("1) Да", callback_data=f"select_sos:1:{user}"),
            InlineKeyboardButton("2) Нет", callback_data=f"select_sos:2:{user}"),
            InlineKeyboardButton("3) Наверное", callback_data=f"select_sos:3:{user}"),
            InlineKeyboardButton("4) Не хочу отвечать", callback_data=f"select_sos:4:{user}")
    )
    bot.send_message(chat_id, "Выберите ответ:", reply_markup=markup)  

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_sos:"))
def check_answer_3(call):
    bot.answer_callback_query(call.id)

    parts = call.data.split(":")
    ans = parts[1]
    user = parts[2]
    chat_id = call.message.chat.id
    print(f"{ans}") 
    if int(ans) == int(correct_answers[3]):
        update_quize_points(user, 1)

    bot.send_message(chat_id, f"Квиз пройден. Сумма баллов: {check_quiz_points(user)}", reply_markup=main_keyboard())

correct_answers_2 = {
    1: "1",
    2: "3",
    3: "1"
}


# Квиз 2: Математика
def quiz2(message):
    user = message.from_user.username
    print(user)
    if is_finished_quiz(user, 2):
        bot.send_message(message.chat.id, "Вы уже участвовали в этом квизе.")
        return

    bot.send_message(message.chat.id, "Квиз 2: Математика")
    bot.send_message(message.chat.id, "Вопрос 1: Сколько будет 5 * 6?")

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("1) 30", callback_data=f"select_num:1:{user}"),
        InlineKeyboardButton("2) 35", callback_data=f"select_num:2:{user}"),
        InlineKeyboardButton("3) 40", callback_data=f"select_num:3:{user}"),
        InlineKeyboardButton("4) 25", callback_data=f"select_num:4:{user}")
    )

    bot.send_message(message.chat.id, "Выберите ответ:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_num:"))
def check_answer_4(call):
    bot.answer_callback_query(call.id)

    parts = call.data.split(":")
    ans = parts[1]
    user = parts[2]
    chat_id = call.message.chat.id
    print(f"{ans}") 
    if ans == correct_answers_2[1]:
        update_quize_points(user, 2)

    bot.send_message(chat_id, "Вопрос 2: Какой квадратный корень из 144?")
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
            InlineKeyboardButton("1) 10", callback_data=f"select_sqrt:1:{user}"),
            InlineKeyboardButton("2) 11", callback_data=f"select_sqrt:2:{user}"),
            InlineKeyboardButton("3) 12", callback_data=f"select_sqrt:3:{user}"),
            InlineKeyboardButton("4) 13", callback_data=f"select_sqrt:4:{user}")
    )
    bot.send_message(chat_id, "Выберите ответ:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_sqrt:"))
def check_answer_5(call):
    bot.answer_callback_query(call.id)

    parts = call.data.split(":")
    ans = parts[1]
    user = parts[2]
    chat_id = call.message.chat.id
    print(f"{ans}") 
    if ans == correct_answers_2[2]:
        update_quize_points(user, 2)

    bot.send_message(chat_id, "Вопрос 3: Чему равно значение числа Пи (π)?")
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
            InlineKeyboardButton("1) 3.1415", callback_data=f"select_pi:1:{user}"),
            InlineKeyboardButton("2) 3.15", callback_data=f"select_pi:2:{user}"),
            InlineKeyboardButton("3) 2.718", callback_data=f"select_pi:3:{user}"),
            InlineKeyboardButton("4) 3.141", callback_data=f"select_pi:4:{user}")
    )
    bot.send_message(chat_id, "Выберите ответ:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_pi:"))
def check_answer_6(call):
    bot.answer_callback_query(call.id)

    parts = call.data.split(":")
    ans = parts[1]
    user = parts[2]
    chat_id = call.message.chat.id
    print(f"{ans}") 
    if ans == correct_answers_2[3]:
        update_quize_points(user, 2)

    bot.send_message(chat_id, f"Квиз пройден. Сумма баллов: {check_quiz_points(user)}", reply_markup=main_keyboard())

# Квиз 3: Кино
def quiz3(message):
    bot.send_message(message.chat.id, "Квиз 3: Кино")
    bot.send_message(message.chat.id, "Вопрос 1: Как называется фильм, в котором персонаж по имени Ганди спасает мир?")
    bot.send_message(message.chat.id, "А) Гладиатор\nБ) Мстители\nВ) Терминатор\nГ) Индийский фильм 'Ганди'")
    bot.register_next_step_handler(message, check_answer_7)

def check_answer_7(message):
    if message.text.lower() == "г":
        bot.send_message(message.chat.id, "Правильно!")
    else:
        bot.send_message(message.chat.id, "Неправильно, правильный ответ: Г) Индийский фильм 'Ганди'")

    bot.send_message(message.chat.id, "Вопрос 2: Какой фильм получил Оскар за лучший фильм в 1994 году?")
    bot.send_message(message.chat.id, "А) Форрест Гамп\nБ) Побег из Шоушенка\nВ) Парк Юрского периода\nГ) Легенда о Тарзане")
    bot.register_next_step_handler(message, check_answer_8)

def check_answer_8(message):
    if message.text.lower() == "а":
        bot.send_message(message.chat.id, "Правильно!")
    else:
        bot.send_message(message.chat.id, "Неправильно, правильный ответ: А) Форрест Гамп")

    bot.send_message(message.chat.id, "Вопрос 3: Какая актриса сыграла роль Джульетты в фильме 'Ромео и Джульетта' (1996)?")
    bot.send_message(message.chat.id, "А) Меган Фокс\nБ) Скарлетт Йоханссон\nВ) Клэр Дейнс\nГ) Дженнифер Лоуренс")
    bot.register_next_step_handler(message, check_answer_9)

def check_answer_9(message):
    if message.text.lower() == "в":
        bot.send_message(message.chat.id, "Правильно!")
    else:
        bot.send_message(message.chat.id, "Неправильно, правильный ответ: В) Клэр Дейнс")

# Квиз 4: Музыка
def quiz4(message):
    bot.send_message(message.chat.id, "Квиз 4: Музыка")
    bot.send_message(message.chat.id, "Вопрос 1: Кто является автором песни 'Bohemian Rhapsody'?")
    bot.send_message(message.chat.id, "А) Элтон Джон\nБ) Фредди Меркьюри\nВ) Лед Зеппелин\nГ) Пол Маккартни")
    bot.register_next_step_handler(message, check_answer_10)

def check_answer_10(message):
    if message.text.lower() == "б":
        bot.send_message(message.chat.id, "Правильно!")
    else:
        bot.send_message(message.chat.id, "Неправильно, правильный ответ: Б) Фредди Меркьюри")

    bot.send_message(message.chat.id, "Вопрос 2: Какой музыкальный инструмент играет на концертах группы Metallica?")
    bot.send_message(message.chat.id, "А) Гитара\nБ) Фортепиано\nВ) Тромбон\nГ) Ударные")
    bot.register_next_step_handler(message, check_answer_11)

def check_answer_11(message):
    if message.text.lower() == "а":
        bot.send_message(message.chat.id, "Правильно!")
    else:
        bot.send_message(message.chat.id, "Неправильно, правильный ответ: А) Гитара")

    bot.send_message(message.chat.id, "Вопрос 3: Как называется дебютный альбом группы The Beatles?")
    bot.send_message(message.chat.id, "А) Abbey Road\nБ) Let It Be\nВ) Please Please Me\nГ) Revolver")
    bot.register_next_step_handler(message, check_answer_12)

def check_answer_12(message):
    if message.text.lower() == "в":
        bot.send_message(message.chat.id, "Правильно!")
    else:
        bot.send_message(message.chat.id, "Неправильно, правильный ответ: В) Please Please Me")

# Квиз 5: Технологии
def quiz5(message):
    bot.send_message(message.chat.id, "Квиз 5: Технологии")
    bot.send_message(message.chat.id, "Вопрос 1: Что из перечисленного является операционной системой?")
    bot.send_message(message.chat.id, "А) Windows\nБ) Google\nВ) Samsung\nГ) Mozilla")
    bot.register_next_step_handler(message, check_answer_13)

def check_answer_13(message):
    if message.text.lower() == "а":
        bot.send_message(message.chat.id, "Правильно!")
    else:
        bot.send_message(message.chat.id, "Неправильно, правильный ответ: А) Windows")

    bot.send_message(message.chat.id, "Вопрос 2: Как называется самая популярная социальная сеть?")
    bot.send_message(message.chat.id, "А) Twitter\nБ) Instagram\nВ) Facebook\nГ) LinkedIn")
    bot.register_next_step_handler(message, check_answer_14)

def check_answer_14(message):
    if message.text.lower() == "в":
        bot.send_message(message.chat.id, "Правильно!")
    else:
        bot.send_message(message.chat.id, "Неправильно, правильный ответ: В) Facebook")

    bot.send_message(message.chat.id, "Вопрос 3: Как называется язык программирования, который был создан для написания сценариев?")
    bot.send_message(message.chat.id, "А) Python\nБ) Ruby\nВ) Java\nГ) JavaScript")
    bot.register_next_step_handler(message, check_answer_15)

def check_answer_15(message):
    if message.text.lower() == "а":
        bot.send_message(message.chat.id, "Правильно!")
    else:
        bot.send_message(message.chat.id, "Неправильно, правильный ответ: А) Python")