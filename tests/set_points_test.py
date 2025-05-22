from unittest.mock import AsyncMock, patch

import pytest
from aiogram.types import CallbackQuery, Message

import src.admin_handlers.set_points as handlers


@pytest.fixture
def dummy_message():
    class U:
        username = "admin"
    msg = AsyncMock(spec=Message)
    msg.from_user = U()
    msg.text = ""
    msg.answer = AsyncMock()
    return msg


@pytest.fixture
def dummy_callback():
    cb = AsyncMock(spec=CallbackQuery)
    cb.message = AsyncMock()
    cb.message.answer = AsyncMock()
    cb.message.delete = AsyncMock()
    cb.answer = AsyncMock()
    cb.data = ""
    return cb


@pytest.fixture
def dummy_state():
    st = AsyncMock()
    st.get_data = AsyncMock(return_value={})
    st.update_data = AsyncMock()
    st.set_state = AsyncMock()
    st.clear = AsyncMock()
    return st


@pytest.fixture(autouse=True)
def patch_db(monkeypatch):
    monkeypatch.setattr(handlers, "get_admin_by_username",
                        AsyncMock(return_value={"username": "admin"}))
    monkeypatch.setattr(handlers, "get_admin_level",
                        AsyncMock(return_value=0))
    monkeypatch.setattr(handlers, "get_user_by_username",
                        AsyncMock(return_value={"username": "user"}))
    monkeypatch.setattr(handlers, "is_quest_started",
                        AsyncMock(return_value=True))
    monkeypatch.setattr(handlers, "update_user_points",
                        AsyncMock())
    monkeypatch.setattr(handlers, "update_user_queststation",
                        AsyncMock())
    monkeypatch.setattr("src.admin_handlers.set_points.STATIONS",
                        {"Station A": 1, "Station B": 2})


@pytest.mark.asyncio
async def test_set_points_no_access(dummy_message, dummy_state):
    handlers.get_admin_by_username.return_value = None
    await handlers.set_points(dummy_message, dummy_state)
    dummy_message.answer.assert_awaited_with(
        "❌ У вас нет доступа к этой команде.")
    dummy_state.set_state.assert_not_awaited()


@pytest.mark.asyncio
async def test_set_points_ok(dummy_message, dummy_state):
    await handlers.set_points(dummy_message, dummy_state)
    dummy_message.answer.assert_awaited_with(
        "Введите ник пользователя (@username):")
    dummy_state.set_state.assert_awaited_with(
        handlers.SetPointsStates.waiting_username)


@pytest.mark.asyncio
async def test_process_username_user_not_found(dummy_message, dummy_state):
    handlers.get_user_by_username.return_value = None
    dummy_message.text = "@noone"
    await handlers.process_username(dummy_message, dummy_state)
    dummy_message.answer.assert_awaited_with("❌ Пользователь noone не найден!")
    dummy_state.clear.assert_awaited()


@pytest.mark.asyncio
async def test_process_username_level0(dummy_message, dummy_state):
    dummy_message.text = "@user"
    await handlers.process_username(dummy_message, dummy_state)
    args, kwargs = dummy_message.answer.call_args
    assert "Выберите номер станции:" in args[0]
    assert "reply_markup" in kwargs
    dummy_state.set_state.assert_awaited_with(
        handlers.SetPointsStates.waiting_station)


@pytest.mark.asyncio
async def test_process_station_selection_already_points(dummy_callback, dummy_state):
    dummy_state.get_data.return_value = {"username": "user"}
    handlers.get_user_by_username.return_value = {"quest1_points": 5}
    dummy_callback.data = "select_station:1"
    await handlers.process_station_selection(dummy_callback, dummy_state)
    dummy_callback.message.answer.assert_awaited_with(
        "❌ Пользователю user уже начислены баллы.")
    dummy_state.clear.assert_awaited()


@pytest.mark.asyncio
async def test_process_station_selection_ok(dummy_callback, dummy_state):
    dummy_state.get_data.return_value = {"username": "user"}
    handlers.get_user_by_username.return_value = {"quest1_points": 0}
    dummy_callback.data = "select_station:1"
    called = {}

    async def fake_pps(msg, username, station_num, state):
        called['ok'] = (msg, username, station_num)
    monkey = patch.object(handlers, "process_points_selection", fake_pps)
    with monkey:
        await handlers.process_station_selection(dummy_callback, dummy_state)
    dummy_callback.answer.assert_awaited()
    dummy_callback.message.answer.assert_any_call("✅ Вы выбрали Station A")
    assert called['ok'][1:] == ("user", 1)


@pytest.mark.asyncio
async def test_process_points_selection_not_started(dummy_message, dummy_state):
    handlers.is_quest_started.return_value = False
    await handlers.process_points_selection(dummy_message, "user", 1, dummy_state)
    dummy_message.answer.assert_awaited_with(
        "❌ Пользователь user ещё не начал квест.")


@pytest.mark.asyncio
async def test_process_points_selection_ok(dummy_message, dummy_state):
    handlers.is_quest_started.return_value = True
    await handlers.process_points_selection(dummy_message, "user", 1, dummy_state)
    args, kwargs = dummy_message.answer.call_args
    assert "Выберите количество баллов для @user:" in args[0]
    assert "reply_markup" in kwargs
    dummy_state.set_state.assert_awaited_with(
        handlers.SetPointsStates.waiting_points)


@pytest.mark.asyncio
async def test_back_to_stations_ok(dummy_callback, dummy_state):
    dummy_callback.data = "back_to_stations:user"
    await handlers.back_to_stations(dummy_callback, dummy_state)
    dummy_callback.message.delete.assert_awaited()
    dummy_callback.message.answer.assert_called()
    dummy_state.set_state.assert_awaited_with(
        handlers.SetPointsStates.waiting_station)


@pytest.mark.asyncio
async def test_process_points_callback_ok(dummy_callback, dummy_state):
    dummy_state.get_data.return_value = {"username": "user", "station_num": 2}
    dummy_callback.data = "points:2"
    dummy_callback.message.answer = AsyncMock()
    await handlers.process_points_callback(dummy_callback, dummy_state)
    dummy_callback.answer.assert_awaited()
    handlers.update_user_points.assert_awaited_with("user", 2, 2)
    handlers.update_user_queststation.assert_awaited_with("user")
    dummy_callback.message.answer.assert_any_call(
        "✅ Пользователю user начислено 2 баллов!")
    dummy_state.clear.assert_awaited()
