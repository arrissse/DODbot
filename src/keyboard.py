from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_keyboard():
    """Возвращает основную клавиатуру пользователя с кнопками расписания, карты и квеста.

    Returns:
        ReplyKeyboardMarkup: Клавиатура с 4 рядами кнопок:
            - Расписание лекций и Карта
            - Активности ФШ и Расположение стендов
            - Квизы
            - Квест
    """
    buttons = [
        ["📅 Расписание лекций", "🗺 Карта"],
        ["🧩 Активности ФШ", "📍 Расположение стендов"],
        ["🎓 Квизы"],
        ["🎯 Квест"]
    ]

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=text) for text in row]
            for row in buttons
        ],
        resize_keyboard=True,
    )


def pro_admin_keyboard():
    """Возвращает расширенное меню администратора (Pro) с возможностями управления.

    Returns:
        ReplyKeyboardMarkup: Клавиатура с 4 рядами кнопок:
            - Таблица пользователей и Проставить баллы
            - Статистика квеста и Рассылка
            - Добавить админа и Мерч
            - Переключение меню и Запуск квиза
    """
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
    """Возвращает клавиатуру администратора Pro для управления мерчем.

    Returns:
        ReplyKeyboardMarkup: Клавиатура с 3 рядами кнопок:
            - Выдача мерча и Настройка стоимости
            - Добавление/Удаление позиций
            - Кнопка возврата
    """
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
    """Возвращает клавиатуру для запуска квизов.

    Returns:
        ReplyKeyboardMarkup: Клавиатура с 3 рядами:
            - Квизы 1-4 в два столбца
            - Квиз 5 и кнопка возврата
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Квиз 1"), KeyboardButton(text="Квиз 2")],
            [KeyboardButton(text="Квиз 3"), KeyboardButton(text="Квиз 4")],
            [KeyboardButton(text="Квиз 5"), KeyboardButton(text="Назад ⬅️")]
        ],
        resize_keyboard=True
    )


def mipt_admin_keyboard():
    """Возвращает клавиатуру MIPT-администратора с базовыми функциями.

    Returns:
        ReplyKeyboardMarkup: Клавиатура с 2 рядами кнопок:
            - Таблица пользователей и Простановка баллов
            - Статистика и Переключение меню
    """
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
    """Возвращает базовую клавиатуру администратора.

    Returns:
        ReplyKeyboardMarkup: Клавиатура с 2 рядами кнопок:
            - Управление пользователями и Мерчем
            - Статистика и Переключение меню
    """
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
    """Возвращает клавиатуру начала квеста.

    Returns:
        ReplyKeyboardMarkup: Однострочная клавиатура с:
            - Кнопки старта квеста и возврата
    """
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="▶️ Начать"),
                   KeyboardButton(text="⬅️ Назад")]],
        resize_keyboard=True
    )


def quest_started_keyboard():
    """Возвращает клавиатуру для продолжения квеста.

    Returns:
        ReplyKeyboardMarkup: Однострочная клавиатура с:
            - Кнопки продолжения квеста и возврата
    """
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="▶️ Продолжить"),
                   KeyboardButton(text="⬅️ Назад")]],
        resize_keyboard=True
    )


def continue_quest_keyboard():
    """Возвращает клавиатуру со списком станций квеста.

    Returns:
        ReplyKeyboardMarkup: Клавиатура с 6 рядами:
            - 11 кнопок станций в два столбца
            - Кнопка возврата в последнем ряду
    """
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
            [KeyboardButton(text="станция ПИШ ФАЛТ"),
             KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )


def activity_keyboard():
    """Возвращает клавиатуру с факультетами для отображения активности.

    Returns:
        ReplyKeyboardMarkup: Клавиатура с 6 рядами:
            - 11 кнопок факультетов в два столбца
            - Кнопка возврата в последнем ряду
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="ФРКТ"), KeyboardButton(text="ЛФИ")],
            [KeyboardButton(text="ФАКТ"), KeyboardButton(text="ФЭФМ")],
            [KeyboardButton(text="ФПМИ"), KeyboardButton(text="ФБМФ")],
            [KeyboardButton(text="КНТ"), KeyboardButton(text="ФБВТ")],
            [KeyboardButton(text="ВШПИ"), KeyboardButton(text="ВШМ")],
            [KeyboardButton(text="ПИШ ФАЛТ"), KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )
