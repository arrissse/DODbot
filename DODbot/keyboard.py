from telebot import types

def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    item1 = types.KeyboardButton("📅 Расписание лекций")
    item2 = types.KeyboardButton("🗺 Карта")
    item3 = types.KeyboardButton("🎯 Квест")
    item4 = types.KeyboardButton("🎓 Квизы")
    markup.add(item1, item2, item3, item4)
    return markup

def pro_admin_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    item1 = types.KeyboardButton("Таблица пользователей")
    item2 = types.KeyboardButton("Квест. Проставить баллы")
    item3 = types.KeyboardButton("Квест. Текущая статистика")
    item4 = types.KeyboardButton("Отправить рассылку")
    item5 = types.KeyboardButton("Добавить админа")
    item6 = types.KeyboardButton("Мерч")
    item7 = types.KeyboardButton("Переключить меню")
    item8 = types.KeyboardButton("Начать квиз")
    markup.add(item1, item2, item3, item4, item5, item6, item7)
    return markup

def pro_admin_merch():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    item1 = types.KeyboardButton("Выдать мерч")
    item2 = types.KeyboardButton("Стоимость мерча")
    item3 = types.KeyboardButton("Добавить позицию мерча")
    item4 = types.KeyboardButton("Удалить позицию мерча")
    item5 = types.KeyboardButton("Назад ⬅️")
    markup.add(item1, item2, item3, item4, item5)
    return markup

def pro_admin_quiz_start():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    item1 = types.KeyboardButton("Квиз 1")
    item2 = types.KeyboardButton("Квиз 2")
    item3 = types.KeyboardButton("Квиз 3")
    item4 = types.KeyboardButton("Квиз 4")
    item5 = types.KeyboardButton("Квиз 5")
    item6 = types.KeyboardButton("Назад ⬅️")
    markup.add(item1, item2, item3, item4, item5, item6)
    return markup

def mipt_admin_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    item1 = types.KeyboardButton("Таблица пользователей")
    item2 = types.KeyboardButton("Квест. Проставить баллы")
    item3 = types.KeyboardButton("Квест. Текущая статистика")
    item4 = types.KeyboardButton("Переключить меню")
    markup.add(item1, item2, item3, item4)
    return markup

def admin_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    item1 = types.KeyboardButton("Таблица пользователей")
    item2 = types.KeyboardButton("Выдать мерч")
    item3 = types.KeyboardButton("Квест. Текущая статистика")
    item4 = types.KeyboardButton("Переключить меню")
    markup.add(item1, item2, item3, item4)
    return markup

def quest_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    item1 = types.KeyboardButton("▶️ Начать")
    item2 = types.KeyboardButton("⬅️ Назад")
    markup.add(item1, item2)
    return markup

def quest_started_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    item1 = types.KeyboardButton("▶️ Продолжить")
    item2 = types.KeyboardButton("⬅️ Назад")
    markup.add(item1, item2)
    return markup

def continue_quest_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    item1 = types.KeyboardButton("станция ФРКТ")
    item2 = types.KeyboardButton("станция ЛФИ")
    item3 = types.KeyboardButton("станция ФАКТ")
    item4 = types.KeyboardButton("станция ФЭФМ")
    item5 = types.KeyboardButton("станция ФПМИ")
    item6 = types.KeyboardButton("станция ФБМФ")
    item7 = types.KeyboardButton("станция КНТ")
    item8 = types.KeyboardButton("станция ФБВТ")
    item9 = types.KeyboardButton("станция ВШПИ")
    item10 = types.KeyboardButton("станция ВШМ")
    item11 = types.KeyboardButton("станция ПИШ РПИ")
    item12 = types.KeyboardButton("⬅️ Назад")
    markup.add(item1, item2, item3, item4, item5, item6, item7, item8, item9, item10, item11, item12)
    return markup