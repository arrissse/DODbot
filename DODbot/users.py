import sqlite3
import openpyxl
import logging
from openpyxl.styles import Font, PatternFill
from typing import Optional, List, Tuple
from database import db_manager  # Используем новый менеджер подключений

# Настройка логгера
logger = logging.getLogger(__name__)


class UserManager:
    @staticmethod
    def create_users_table():
        """Создание таблицы пользователей с улучшенной структурой"""
        try:
            with db_manager.get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        username TEXT UNIQUE,
                        quest_started INTEGER DEFAULT 0 CHECK(quest_started IN (0, 1)),
                        quest1_points INTEGER DEFAULT 0,
                        quest2_points INTEGER DEFAULT 0,
                        quest3_points INTEGER DEFAULT 0,
                        quest4_points INTEGER DEFAULT 0,
                        quest5_points INTEGER DEFAULT 0,
                        quest6_points INTEGER DEFAULT 0,
                        quest7_points INTEGER DEFAULT 0,
                        quest8_points INTEGER DEFAULT 0,
                        quest9_points INTEGER DEFAULT 0,
                        quest10_points INTEGER DEFAULT 0,
                        quest11_points INTEGER DEFAULT 0,
                        quest_station INTEGER DEFAULT 0 CHECK(quest_station BETWEEN 0 AND 11),
                        quest_points INTEGER DEFAULT 0,
                        quiz_points INTEGER DEFAULT 0,
                        quiz_1 INTEGER DEFAULT 0,
                        quiz_2 INTEGER DEFAULT 0,
                        quiz_3 INTEGER DEFAULT 0,
                        quiz_4 INTEGER DEFAULT 0,
                        quiz_5 INTEGER DEFAULT 0
                    )
                """)
                conn.commit()
                logger.info("Таблица users успешно создана")
        except Exception as e:
            logger.error(f"Ошибка создания таблицы users: {e}")
            raise

    @staticmethod
    def add_user(user_id: int, username: str) -> bool:
        """Добавление нового пользователя"""
        try:
            with db_manager.get_connection() as conn:
                conn.execute(
                    "INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)",
                    (user_id, username))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка добавления пользователя {username}: {e}")
            return False

    @staticmethod
    def get_user_by_username(username: str) -> Optional[Tuple]:
        """Получение пользователя по username"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM users WHERE username = ?", (username,))
                return cursor.fetchone()
        except Exception as e:
            logger.error(f"Ошибка получения пользователя {username}: {e}")
            return None

    @staticmethod
    def get_all_users() -> List[Tuple]:
        """Получение списка всех пользователей"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.execute("SELECT * FROM users ORDER BY id")
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Ошибка получения списка пользователей: {e}")
            return []

    @staticmethod
    def update_quest_status(username: str, started: bool = True) -> bool:
        """Обновление статуса квеста"""
        try:
            with db_manager.get_connection() as conn:
                conn.execute(
                    "UPDATE users SET quest_started = ? WHERE username = ?",
                    (1 if started else 0, username))
                conn.commit()
                return True
        except Exception as e:
            logger.error(
                f"Ошибка обновления статуса квеста для {username}: {e}")
            return False

    @staticmethod
    def update_quest_points(username: str, station: int, points: int) -> bool:
        """Обновление баллов за станцию квеста"""
        if not 1 <= station <= 11:
            logger.error(f"Некорректный номер станции: {station}")
            return False

        try:
            with db_manager.get_connection() as conn:
                # Обновление баллов для конкретной станции
                conn.execute(
                    f"UPDATE users SET quest{station}_points = ? WHERE username = ?",
                    (points, username))

                    # Обновление общего количества баллов
                conn.execute(
                        "UPDATE users SET quest_points = quest_points + ? WHERE username = ?",
                        (points, username))

                        # Обновление счетчика станций
                conn.execute("""
                    UPDATE users SET quest_station = (
                        SELECT COUNT(*) FROM (
                            SELECT quest1_points, quest2_points, quest3_points,
                                   quest4_points, quest5_points, quest6_points,
                                   quest7_points, quest8_points, quest9_points,
                                   quest10_points, quest11_points
                        ) WHERE value > 0
                    )
                    WHERE username = ?
                """, (username,))

                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка обновления баллов для {username}: {e}")
            return False

    @staticmethod
    def update_quize_points(username: str, quiz_num: int, points: int) -> bool:
        """Обновление баллов за квиз"""
        if not 1 <= quiz_num <= 5:
            logger.error(f"Некорректный номер квиза: {quiz_num}")
            return False

        try:
            with db_manager.get_connection() as conn:
                # Обновление конкретного квиза
                conn.execute(
                    f"UPDATE users SET quiz_{quiz_num} = ? WHERE username = ?",
                    (points, username))

                    # Обновление общего количества баллов
                conn.execute(
                        "UPDATE users SET quiz_points = quiz_points + ? WHERE username = ?",
                        (points, username))

                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка обновления баллов квиза для {username}: {e}")
            return False

    @staticmethod
    def save_users_to_excel(filename: str = "users.xlsx") -> Optional[str]:
        """Экспорт пользователей в Excel с улучшенным форматированием"""
        try:
            users = UserManager.get_all_users()
            if not users:
                logger.warning("Нет данных для экспорта")
                return None

            workbook = openpyxl.Workbook()
            sheet = workbook.active
            sheet.title = "Пользователи"

            # Заголовки
            headers = [
                "ID", "Username", "Участие в квесте",
                *[f"Станция {i}" for i in range(1, 12)],
                "Пройдено станций", "Общие баллы",
                "Баллы за квизы", *[f"Квиз {i}" for i in range(1, 6)]
            ]
            sheet.append(headers)

            # Данные
            for user in users:
                sheet.append(user)

            # Стилизация
            header_fill = PatternFill(
                start_color="4F81BD", end_color="4F81BD", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF")

            for col in range(1, len(headers) + 1):
                cell = sheet.cell(row=1, column=col)
                cell.fill = header_fill
                cell.font = header_font

            # Автонастройка ширины столбцов
            for column in sheet.columns:
                max_length = 0
                column = [cell for cell in column]
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except:
                        pass
                adjusted_width = (max_length + 2) * 1.2
                sheet.column_dimensions[column[0].column_letter].width = adjusted_width

            workbook.save(filename)
            return filename

        except Exception as e:
            logger.error(f"Ошибка экспорта в Excel: {e}")
            return None

    @staticmethod
    def get_quest_progress(username: str) -> dict:
        """Получение прогресса по квесту"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT quest_started, quest_station, quest_points,
                           quest1_points, quest2_points, quest3_points,
                           quest4_points, quest5_points, quest6_points,
                           quest7_points, quest8_points, quest9_points,
                           quest10_points, quest11_points
                    FROM users WHERE username = ?
                """, (username,))
                result = cursor.fetchone()

                if not result:
                    return {}

                return {
                    "started": bool(result[0]),
                    "stations_completed": result[1],
                    "total_points": result[2],
                    "stations": {
                        f"station_{i}": result[i+3] for i in range(11)
                    }
                }
        except Exception as e:
            logger.error(f"Ошибка получения прогресса для {username}: {e}")
            return {}

    @staticmethod
    def get_quiz_progress(username: str) -> dict:
        """Получение прогресса по квизам"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT quiz_points, quiz_1, quiz_2, 
                           quiz_3, quiz_4, quiz_5
                    FROM users WHERE username = ?
                """, (username,))
                result = cursor.fetchone()

                if not result:
                    return {}

                return {
                    "total_points": result[0],
                    "quizzes": {
                        f"quiz_{i}": result[i+1] for i in range(5)
                    }
                }
        except Exception as e:
            logger.error(
                f"Ошибка получения прогресса квизов для {username}: {e}")
            return {}
