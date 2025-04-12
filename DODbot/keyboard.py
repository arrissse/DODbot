from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Расписание лекций"),
             KeyboardButton(text="🗺 Карта")],
            [KeyboardButton(text="🧩 Активности ФШ"),
             KeyboardButton(text="🎓 Квизы")],
            [KeyboardButton(text="📍 Расположение стендов"),
             KeyboardButton(text="🎯 Квест")]
        ],
        resize_keyboard=True
    )


def pro_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Таблица пользователей"),
             KeyboardButton(text="Квест. Проставить баллы")],
            [KeyboardButton(text="Квест. Текущая статистика"),
             KeyboardButton(text="Отправить рассылку")],
            [KeyboardButton(text="Добавить админа"),
             KeyboardButton(text="Мерч")],
            [KeyboardButton(text="Переключить меню"),
             KeyboardButton(text="Начать квиз")]
        ],
        resize_keyboard=True
    )


def pro_admin_merch():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Выдать мерч"),
             KeyboardButton(text="Стоимость мерча")],
            [KeyboardButton(text="Добавить позицию мерча"),
             KeyboardButton(text="Удалить позицию мерча")],
            [KeyboardButton(text="Назад ⬅️")]
        ],
        resize_keyboard=True
    )


def pro_admin_quiz_start():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Квиз 1"), KeyboardButton(text="Квиз 2")],
            [KeyboardButton(text="Квиз 3"), KeyboardButton(text="Квиз 4")],
            [KeyboardButton(text="Квиз 5"), KeyboardButton(text="Назад ⬅️")]
        ],
        resize_keyboard=True
    )


def mipt_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Таблица пользователей"),
             KeyboardButton(text="Квест. Проставить баллы")],
            [KeyboardButton(text="Квест. Текущая статистика"),
             KeyboardButton(text="Переключить меню")]
        ],
        resize_keyboard=True
    )


def admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Таблица пользователей"),
             KeyboardButton(text="Выдать мерч")],
            [KeyboardButton(text="Квест. Текущая статистика"),
             KeyboardButton(text="Переключить меню")]
        ],
        resize_keyboard=True
    )


def quest_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="▶️ Начать"),
                   KeyboardButton(text="⬅️ Назад")]],
        resize_keyboard=True
    )


def quest_started_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="▶️ Продолжить"),
                   KeyboardButton(text="⬅️ Назад")]],
        resize_keyboard=True
    )


def continue_quest_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="станция ФРКТ"),
             KeyboardButton(text="станция ЛФИ")],
            [KeyboardButton(text="станция ФАКТ"),
             KeyboardButton(text="станция ФЭФМ")],
            [KeyboardButton(text="станция ФПМИ"),
             KeyboardButton(text="станция ФБМФ")],
            [KeyboardButton(text="станция КНТ"),
             KeyboardButton(text="станция ФБВТ")],
            [KeyboardButton(text="станция ВШПИ"),
             KeyboardButton(text="станция ВШМ")],
            [KeyboardButton(text="станция ПИШ РПИ"),
             KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )


def activity_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="ФРКТ"), KeyboardButton(text="ЛФИ")],
            [KeyboardButton(text="ФАКТ"), KeyboardButton(text="ФЭФМ")],
            [KeyboardButton(text="ФПМИ"), KeyboardButton(text="ФБМФ")],
            [KeyboardButton(text="КНТ"), KeyboardButton(text="ФБВТ")],
            [KeyboardButton(text="ВШПИ"), KeyboardButton(text="ВШМ")],
            [KeyboardButton(text="ПИШ РПИ"), KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )
