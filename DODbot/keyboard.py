from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton(text="📅 Расписание лекций"),
        KeyboardButton(text="🗺 Карта"),
        KeyboardButton(text="🧩 Активности ФШ"),
        KeyboardButton(text="🎓 Квизы"),
        KeyboardButton(text="📍 Расположение стендов"),
        KeyboardButton(text="🎯 Квест")
    ]
    markup.add(*buttons)
    return markup


def pro_admin_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton(text="Таблица пользователей"),
        KeyboardButton(text="Квест. Проставить баллы"),
        KeyboardButton(text="Квест. Текущая статистика"),
        KeyboardButton(text="Отправить рассылку"),
        KeyboardButton(text="Добавить админа"),
        KeyboardButton(text="Мерч"),
        KeyboardButton(text="Переключить меню"),
        KeyboardButton(text="Начать квиз")
    ]
    markup.add(*buttons)
    return markup


def pro_admin_merch():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton(text="Выдать мерч"),
        KeyboardButton(text="Стоимость мерча"),
        KeyboardButton(text="Добавить позицию мерча"),
        KeyboardButton(text="Удалить позицию мерча"),
        KeyboardButton(text="Назад ⬅️")
    ]
    markup.add(*buttons)
    return markup


def pro_admin_quiz_start():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton(text="Квиз 1"),
        KeyboardButton(text="Квиз 2"),
        KeyboardButton(text="Квиз 3"),
        KeyboardButton(text="Квиз 4"),
        KeyboardButton(text="Квиз 5"),
        KeyboardButton(text="Назад ⬅️")
    ]
    markup.add(*buttons)
    return markup


def mipt_admin_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton(text="Таблица пользователей"),
        KeyboardButton(text="Квест. Проставить баллы"),
        KeyboardButton(text="Квест. Текущая статистика"),
        KeyboardButton(text="Переключить меню")
    ]
    markup.add(*buttons)
    return markup


def admin_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton(text="Таблица пользователей"),
        KeyboardButton(text="Выдать мерч"),
        KeyboardButton(text="Квест. Текущая статистика"),
        KeyboardButton(text="Переключить меню")
    ]
    markup.add(*buttons)
    return markup


def quest_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton(text="▶️ Начать"),
        KeyboardButton(text="⬅️ Назад")
    ]
    markup.add(*buttons)
    return markup


def quest_started_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton(text="▶️ Продолжить"),
        KeyboardButton(text="⬅️ Назад")
    ]
    markup.add(*buttons)
    return markup


def continue_quest_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton(text="станция ФРКТ"),
        KeyboardButton(text="станция ЛФИ"),
        KeyboardButton(text="станция ФАКТ"),
        KeyboardButton(text="станция ФЭФМ"),
        KeyboardButton(text="станция ФПМИ"),
        KeyboardButton(text="станция ФБМФ"),
        KeyboardButton(text="станция КНТ"),
        KeyboardButton(text="станция ФБВТ"),
        KeyboardButton(text="станция ВШПИ"),
        KeyboardButton(text="станция ВШМ"),
        KeyboardButton(text="станция ПИШ РПИ"),
        KeyboardButton(text="⬅️ Назад")
    ]
    markup.add(*buttons)
    return markup


def activity_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton(text="ФРКТ"),
        KeyboardButton(text="ЛФИ"),
        KeyboardButton(text="ФАКТ"),
        KeyboardButton(text="ФЭФМ"),
        KeyboardButton(text="ФПМИ"),
        KeyboardButton(text="ФБМФ"),
        KeyboardButton(text="КНТ"),
        KeyboardButton(text="ФБВТ"),
        KeyboardButton(text="ВШПИ"),
        KeyboardButton(text="ВШМ"),
        KeyboardButton(text="ПИШ РПИ"),
        KeyboardButton(text="⬅️ Назад")
    ]
    markup.add(*buttons)
    return markup
