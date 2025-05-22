import asyncio
from unittest.mock import AsyncMock

import aiosqlite
import pytest
import pytest_asyncio
from openpyxl import load_workbook

import database.base as _db_mod
import database.users as users_mod


class InMemoryConn:
    """
    Контекстный менеджер для работы с in-memory соединением aiosqlite.
    Используется для подмены get_connection() в тестах.
    """

    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, exc_type, exc, exc_tb):
        pass


@pytest_asyncio.fixture(autouse=True)
async def in_memory_db(monkeypatch):
    """Monkeypatch db_manager.get_connection to return an async‐CM.

    Args:
        monkeypatch: pytest's monkeypatch fixture.

    Yields:
        None. Tears down DB connection after test.
    """
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row

    def get_connection():
        return InMemoryConn(conn)

    monkeypatch.setattr(_db_mod.db_manager, "get_connection", get_connection)
    yield
    await conn.close()


@pytest.mark.asyncio
async def test_create_and_add_and_fetch_user():
    """
    Проверяет создание таблицы пользователей, добавление, повторное добавление и получение.
    """
    await users_mod.create_users_table()

    result = await users_mod.add_user(123, "alice")
    assert result is True

    result2 = await users_mod.add_user(123, "alice")
    assert result2 is False

    user = await users_mod.get_user_by_username("alice")
    assert user["id"] == 123 and user["username"] == "alice"

    all_u = await users_mod.get_all_users()
    assert isinstance(all_u, list) and len(all_u) == 1
    assert all_u[0]["username"] == "alice"


@pytest.mark.asyncio
async def test_points_and_merch_operations():
    """
    Проверяет работу с баллами за станции и мерч.
    """
    await users_mod.create_users_table()
    await users_mod.add_user(2, "carol")

    assert await users_mod.check_points("carol") == 0
    assert await users_mod.check_st_points("carol", 3) in (0, None)

    await users_mod.update_user_points("carol", 3, 5)
    assert await users_mod.check_points("carol") == 5
    assert await users_mod.check_st_points("carol", 3) == 5

    await users_mod.update_merch_points("carol", 2)
    assert await users_mod.check_points("carol") == 3


@pytest.mark.asyncio
async def test_counters(monkeypatch):
    """
    Проверяет счётчики квестов: активных и завершённых.

    Args:
        monkeypatch: pytest's monkeypatch fixture.
    """
    await users_mod.create_users_table()
    await users_mod.add_user(10, "u1")
    await users_mod.add_user(11, "u2")

    await users_mod.start_quest("u1")
    assert await users_mod.count_active_quests() == 1

    async def fake_merch(user):
        return user == "u2"
    monkeypatch.setattr(users_mod, "is_got_any_merch", fake_merch)

    finished = await users_mod.count_finished_quests()
    assert finished == 1


@pytest.mark.asyncio
async def test_quest_start_and_finish_flags():
    """
    Проверяет флаг начала квеста у пользователя.
    """

    await users_mod.create_users_table()
    await users_mod.add_user(1, "bob")

    assert not await users_mod.is_quest_started("bob")

    await users_mod.start_quest("bob")
    assert await users_mod.is_quest_started("bob")


@pytest.mark.asyncio
async def test_quiz_points_and_completion(monkeypatch):
    """
    Проверяет начисление баллов за викторины и завершение квеста после викторины.

    Args:
        monkeypatch: pytest's monkeypatch fixture.
    """
    await users_mod.create_users_table()
    await users_mod.add_user(3, "dan")

    fuser = AsyncMock(return_value=True)
    monkeypatch.setattr(users_mod, "is_got_any_merch", fuser)

    assert await users_mod.check_quiz_points("dan", 1) in (0, None)
    assert not await users_mod.is_finished_quiz("dan", 1)

    await users_mod.update_quize_points("dan", 1)
    assert await users_mod.check_quiz_points("dan", 1) == 1
    assert await users_mod.is_finished_quiz("dan", 1)

    assert await users_mod.is_quest_finished("dan")


def test_save_users_to_excel(tmp_path, monkeypatch):
    """
    Проверяет экспорт списка пользователей в Excel-файл.

    Args:
        tmp_path: временный путь для сохранения файла.
        monkeypatch: фикстура для замены get_all_users.
    """
    sample = [
        {
            "id": 101, "username": "x",
            **{f"quest{i}_points": 0 for i in range(1, 12)},
            "quest_station": 0, "quest_points": 0,
            "quize_points": 0, **{f"quize_{i}": 0 for i in range(1, 6)}
        },
        {
            "id": 102, "username": "y",
            **{f"quest{i}_points": i for i in range(1, 12)},
            "quest_station": 11, "quest_points": 66,
            "quize_points": 5, **{f"quize_{i}": 1 for i in range(1, 6)}
        },
    ]
    monkeypatch.setattr(
        users_mod,
        "get_all_users",
        AsyncMock(return_value=sample)
    )

    monkeypatch.chdir(tmp_path)
    filename = asyncio.get_event_loop().run_until_complete(users_mod.save_users_to_excel())
    assert filename == "users.xlsx"
    workbook = load_workbook(tmp_path / filename)
    worksheet = workbook.active

    hdrs = [c.value for c in worksheet[1]]
    assert hdrs[:2] == ["ID", "Username"]

    row2 = [c.value for c in worksheet[2]]
    assert row2[0] == 101 and row2[1] == "x"

    row3 = [c.value for c in worksheet[3]]
    assert row3[0] == 102 and row3[1] == "y"
