from unittest.mock import AsyncMock

import pytest

import src.user_handlers.handlers as handlers


class DummyChat:
    def __init__(self, id):
        self.id = id

class DummyUser:
    def __init__(self, username):
        self.username = username

class DummyMessage:
    def __init__(self, text, user_username="tester", chat_id=42):
        self.text = text
        self.from_user = DummyUser(user_username)
        self.chat = DummyChat(chat_id)
        self.answer = AsyncMock()
        self.answer_photo = AsyncMock()


class DummyCallback:
    def __init__(self, data, message: DummyMessage):
        self.data = data
        self.message = message
        self.answer = AsyncMock()

@pytest.fixture(autouse=True)
def patch_db(monkeypatch):
    monkeypatch.setattr(handlers, "get_all_users", AsyncMock(return_value=[]))
    monkeypatch.setattr(handlers, "add_user", AsyncMock())
    monkeypatch.setattr(handlers, "get_all_admins", AsyncMock(return_value=[]))
    monkeypatch.setattr(handlers, "get_admin_level", AsyncMock(return_value=0))
    monkeypatch.setattr(handlers, "is_quest_started",
                        AsyncMock(return_value=False))
    monkeypatch.setattr(handlers, "start_quest", AsyncMock())
    monkeypatch.setattr(handlers, "check_points", AsyncMock(return_value=5))
    monkeypatch.setattr(handlers, "check_st_points", AsyncMock(return_value=2))

@pytest.mark.asyncio
async def test_start_handler_new_user():
    msg = DummyMessage("/start")
    handlers.get_all_users.return_value = []
    await handlers.start_handler(msg)
    handlers.add_user.assert_awaited_with(42, "tester")
    msg.answer.assert_awaited()

@pytest.mark.asyncio
async def test_start_handler_existing_admin():
    msg = DummyMessage("/start 05")
    handlers.get_all_users.return_value = [msg.from_user]
    handlers.get_all_admins.return_value = [("@tester",)]
    handlers.get_admin_level.return_value = 1

    await handlers.start_handler(msg)
    handlers.add_user.assert_not_awaited()
    msg.answer.assert_awaited()

@pytest.mark.asyncio
async def test_send_schedule_photo():
    msg = DummyMessage("📅 Расписание лекций")
    await handlers.send_schedule_photo(msg)
    msg.answer_photo.assert_awaited()

@pytest.mark.asyncio
async def test_do_action_success(tmp_path):
    file = tmp_path / "test.png"
    file.write_bytes(b"123")
    msg = DummyMessage("ignored")
    await handlers.do_action(msg, str(file))
    msg.answer_photo.assert_awaited()

@pytest.mark.asyncio
async def test_do_action_fail():
    msg = DummyMessage("ignored")
    msg.answer_photo = AsyncMock()
    await handlers.do_action(msg, "no_such_file.png")
    msg.answer_photo.assert_awaited()

@pytest.mark.asyncio
async def test_quest_handler_not_started():
    msg = DummyMessage("🎯 Квест")
    handlers.is_quest_started.return_value = False
    await handlers.quest_handler(msg)
    msg.answer.assert_awaited()

@pytest.mark.asyncio
async def test_quest_handler_started():
    msg = DummyMessage("🎯 Квест")
    handlers.is_quest_started.return_value = True
    await handlers.quest_handler(msg)
    msg.answer.assert_awaited()

@pytest.mark.asyncio
async def test_start_quest_handler():
    msg = DummyMessage("▶️ Начать")
    await handlers.start_quest_handler(msg)
    handlers.start_quest.assert_awaited_with("tester")
    msg.answer.assert_awaited()

@pytest.mark.asyncio
async def test_continue_and_back():
    msg = DummyMessage("▶️ Продолжить")
    await handlers.continue_quest_handler(msg)
    msg.answer.assert_awaited()

    await handlers.back_handler(msg)
    msg.answer.assert_awaited()

@pytest.mark.asyncio
async def test_send_quest_points():
    msg = DummyMessage("ignored")
    await handlers.send_quest_points(msg, "tester", "1")
    msg.answer.assert_awaited_with(
        "Всего баллов: 5\nБаллы за станцию: 2",
        reply_markup=handlers.quest_started_keyboard()
    )

@pytest.mark.asyncio
async def test_handle_station_valid():
    msg = DummyMessage("станция ФРКТ")
    await handlers.handle_station(msg)
    msg.answer.assert_awaited()

@pytest.mark.asyncio
async def test_send_code_and_pts():
    msg = DummyMessage("ignored")
    cb = DummyCallback("code:tester", msg)
    await handlers.send_code(cb)
    msg.answer.assert_awaited()
    cb.answer.assert_awaited()

    cb.data = "pts:tester:3"
    await handlers.send_pts(cb)
    msg.answer.assert_awaited()
    cb.answer.assert_awaited()

@pytest.mark.asyncio
async def test_map_and_stands():
    msg = DummyMessage("🗺 Карта")
    await handlers.send_map_photo(msg)
    msg.answer_photo.assert_awaited()

    msg = DummyMessage("📍 Расположение стендов")
    await handlers.send_stands_photo(msg)
    msg.answer_photo.assert_awaited()

@pytest.mark.asyncio
async def test_school_and_activity():
    msg = DummyMessage("🧩 Активности ФШ")
    await handlers.school_handler(msg)
    msg.answer.assert_awaited()

    msg = DummyMessage("ФРКТ")
    await handlers.handle_activity(msg)
    msg.answer_photo.assert_awaited()
