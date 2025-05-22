from unittest.mock import AsyncMock

import pytest

import src.admin_handlers.add_admin as handlers


class DummyMessage:
    def __init__(self, text, username="master", chat_id=123):
        self.text = text
        self.from_user = type("U", (), {"username": username})
        self.chat = type("C", (), {"id": chat_id})
        self.bot = AsyncMock()
        self.answer = AsyncMock()


class DummyCallback:
    def __init__(self, data, message):
        self.data = data
        self.message = message
        self.answer = AsyncMock()


class DummyState:
    def __init__(self):
        self.storage = {}
        self.set_state = AsyncMock()
        self.update_data = AsyncMock()
        self.get_data = AsyncMock(return_value={})
        self.clear = AsyncMock()


@pytest.fixture(autouse=True)
def patch_db(monkeypatch):
    monkeypatch.setattr(handlers, "get_admin_by_username",
                        AsyncMock(return_value="@master"))
    monkeypatch.setattr(handlers, "get_admin_level", AsyncMock(return_value=0))
    monkeypatch.setattr(handlers, "add_admin", AsyncMock())
    monkeypatch.setattr(handlers, "update_admin_questnum", AsyncMock())
    monkeypatch.setattr(handlers, "get_user_by_username",
                        AsyncMock(return_value={"id": 555}))
    yield


@pytest.mark.asyncio
async def test_new_admin_allowed_sets_username_state():
    msg = DummyMessage("Добавить админа", username="master")
    state = DummyState()

    await handlers.new_admin(msg, state)

    msg.answer.assert_awaited_once_with(
        "Введите ник пользователя (@username):")
    state.set_state.assert_awaited_once_with(
        handlers.AdminStates.waiting_username)


@pytest.mark.asyncio
async def test_new_admin_forbidden_shows_error():
    handlers.get_admin_by_username.return_value = None
    msg = DummyMessage("Добавить админа", username="nope")
    state = DummyState()

    await handlers.new_admin(msg, state)

    msg.answer.assert_awaited_once_with("❌ У вас нет доступа к этой команде.")
    state.set_state.assert_not_called()


@pytest.mark.asyncio
async def test_process_name_prompts_level_and_updates_data():
    msg = DummyMessage("@alice", username="master")
    state = DummyState()

    await handlers.process_name(msg, state)

    state.update_data.assert_awaited_once_with(username="@alice")
    msg.answer.assert_awaited_once_with(
        "Введите уровень админства (0 - pro-admin, 1 - выдача мерча, 2 - админ фш):"
    )
    state.set_state.assert_awaited_once_with(
        handlers.AdminStates.waiting_level)


@pytest.mark.asyncio
async def test_process_level_invalid_clears_state_and_errors():
    msg = DummyMessage("bad", username="master")
    state = DummyState()
    state.get_data.return_value = {"username": "@bob"}

    await handlers.process_level(msg, state)

    msg.answer.assert_awaited_once_with(
        "❌ Некорректный уровень админства. Используйте 0, 1 или 2.")
    state.clear.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_level_zero_creates_admin_and_clears():
    msg = DummyMessage("0", username="master")
    state = DummyState()
    state.get_data.return_value = {"username": "@bob"}

    await handlers.process_level(msg, state)

    handlers.add_admin.assert_awaited_once_with("@bob", 0)
    msg.answer.assert_any_await(f"✅ Админ @bob уровня 0 добавлен.")
    state.clear.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_level_two_prompts_station_selection():
    msg = DummyMessage("2", username="master")
    state = DummyState()
    state.get_data.return_value = {"username": "@carol"}

    await handlers.process_level(msg, state)

    called = msg.answer.call_args.kwargs.get("reply_markup")
    assert called is not None, "Expected a reply_markup with stations"
    state.set_state.assert_awaited_once_with(
        handlers.AdminStates.waiting_station)


@pytest.mark.asyncio
async def test_process_number_creates_and_assigns_station():
    dummy_msg = DummyMessage("", username="master")
    cb = DummyCallback("select_station:3:@dave:2", dummy_msg)
    state = DummyState()

    await handlers.process_number(cb, state)

    handlers.add_admin.assert_awaited_with("@dave", "2")
    handlers.update_admin_questnum.assert_awaited_with("@dave", 3)
    dummy_msg.answer.assert_any_await("✅ Админу @dave назначена станция №3.")
    state.clear.assert_awaited_once()
