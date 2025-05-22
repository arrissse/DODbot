from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import FSInputFile

import src.admin_handlers.merch_handlers as handlers

pytest_plugins = ("pytest_asyncio",)


class DummyConn:
    """Async-CM, который покрывает `fetchrow`, `execute(...).fetchone()`, и `cursor().execute().fetchone()`."""

    def __init__(self, row):
        self._row = row

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def fetchrow(self, *args, **kwargs):
        return self._row

    async def execute(self, sql, params=None):
        class _C:
            def __init__(self, row):
                self._row = row

            async def fetchone(self):
                return self._row
        return _C(self._row)

    async def cursor(self):
        parent = self

        class _Cur:
            def __init__(self, row):
                self._row = row

            async def execute(self, sql, params=None):
                return self

            async def fetchone(self):
                return self._row
        return _Cur(self._row)


class DummyMessage:
    def __init__(self, chat_id=42, username="ivan"):
        self.chat = MagicMock(id=chat_id)
        self.from_user = MagicMock(username=username)
        self.answer = AsyncMock()
        self.answer_document = AsyncMock()


class DummyCallback:
    def __init__(self, data, message):
        self.data = data
        self.message = message
        self.answer = AsyncMock()


@pytest.fixture(autouse=True)
def patch_merch_and_quiz_db(monkeypatch):
    monkeypatch.setattr(handlers, "get_admin_by_username",
                        AsyncMock(return_value=["@ivan", 0]))
    monkeypatch.setattr(handlers, "get_admin_level",
                        AsyncMock(return_value=0))
    monkeypatch.setattr(handlers, "save_merch_to_excel",
                        AsyncMock(return_value="merch.xlsx"))
    monkeypatch.setattr(handlers, "save_admins_to_excel",
                        AsyncMock(return_value="admins.xlsx"))
    monkeypatch.setattr(handlers, "give_merch",            AsyncMock())
    monkeypatch.setattr(handlers, "is_got_merch",
                        AsyncMock(return_value=False))
    monkeypatch.setattr(handlers, "got_merch",
                        AsyncMock(return_value=False))
    monkeypatch.setattr(handlers, "check_points",
                        AsyncMock(return_value=10))
    monkeypatch.setattr(handlers, "update_merch_points",   AsyncMock())
    monkeypatch.setattr(handlers, "get_user_by_username",
                        AsyncMock(return_value={"username": "ivan"}))
    monkeypatch.setattr(handlers, "update_quiz_time", AsyncMock())

    monkeypatch.setattr(handlers, "get_merch_types",
                        AsyncMock(return_value=["Раскрасить шоппер"]))
    monkeypatch.setattr(handlers, "get_merch_price", AsyncMock(return_value=5))

    class DummyDBFactory:
        def __init__(self, row):
            self._row = row
        def get_connection(self):
            return DummyConn(self._row)

    monkeypatch.setattr(handlers, "db_manager", DummyDBFactory(("Quiz 1",)))

@pytest.fixture
def dummy_message():
    return DummyMessage()


@pytest.fixture
def dummy_callback(dummy_message):
    return DummyCallback("start_quiz:1", dummy_message)

@pytest.mark.asyncio
async def test_send_admins_list_as_admin(dummy_message):
    dummy_message.text = "/admins"
    await handlers.send_admins_list(dummy_message)
    dummy_message.answer_document.assert_awaited_once()
    fsfile = dummy_message.answer_document.call_args[0][0]
    assert isinstance(fsfile, FSInputFile)
    assert "admins.xlsx" in fsfile.path


@pytest.mark.asyncio
async def test_send_admins_list_no_access(dummy_message):
    handlers.get_admin_by_username.return_value = None
    dummy_message.text = "/admins"
    await handlers.send_admins_list(dummy_message)
    dummy_message.answer.assert_awaited_with(
        "❌ У вас нет доступа к этой команде.")


@pytest.mark.asyncio
async def test_send_merch_list_as_admin(dummy_message):
    dummy_message.text = "/merch"
    await handlers.send_merch_list(dummy_message)
    dummy_message.answer_document.assert_awaited_once()
    fsfile = dummy_message.answer_document.call_args[0][0]
    assert isinstance(fsfile, FSInputFile)
    assert "merch.xlsx" in fsfile.path


@pytest.mark.asyncio
async def test_send_merch_list_no_access(dummy_message):
    handlers.get_admin_by_username.return_value = None
    dummy_message.text = "/merch"
    await handlers.send_merch_list(dummy_message)
    dummy_message.answer.assert_awaited_with(
        "❌ У вас нет доступа к этой команде.")


@pytest.mark.asyncio
async def test_pro_admin_merch_button_ok(dummy_message):
    dummy_message.text = "Мерч"
    await handlers.pro_admin_merch_button(dummy_message)
    dummy_message.answer.assert_awaited_once()
    assert "reply_markup" in dummy_message.answer.call_args[1]


@pytest.mark.asyncio
async def test_handle_quiz_start_builds_buttons(dummy_message):
    dummy_message.text = "Квиз 1"
    await handlers.handle_quiz_start(dummy_message)
    dummy_message.answer.assert_awaited_once()
    text = dummy_message.answer.call_args[0][0]
    assert "Начать Квиз 1?" in text
    assert "reply_markup" in dummy_message.answer.call_args[1]


@pytest.mark.asyncio
async def test_start_quiz_callback_found(monkeypatch):
    monkeypatch.setattr(handlers, "db_manager", type("X", (), {
        "get_connection": lambda self: DummyConn(("Quiz 1",))
    })())

    msg = DummyMessage()
    cb = DummyCallback("start_quiz:123", msg)

    await handlers.start_quiz(cb)

    cb.answer.assert_awaited_once()
    msg.answer.assert_awaited_once_with("✅ Quiz 1 начат!")


@pytest.mark.asyncio
async def test_start_quiz_callback_not_found(monkeypatch):
    """
    Если в БД нет строки, должен:
      1) вызвать call.answer()
      2) отправить "Ошибка: квиз не найден."
    """
    monkeypatch.setattr(handlers, "db_manager", type("X", (), {
        "get_connection": lambda self: DummyConn(None)
    })())

    msg = DummyMessage()
    cb = DummyCallback("start_quiz:999", msg)

    await handlers.start_quiz(cb)

    cb.answer.assert_awaited_once()
    msg.answer.assert_awaited_once_with("Ошибка: квиз не найден.")

@pytest.mark.asyncio
async def test_give_merch_to_user_and_process(dummy_message):
    dummy_message.text = "Выдать мерч"
    fake_state = AsyncMock()
    await handlers.give_merch_to_user(dummy_message, fake_state)
    dummy_message.answer.assert_awaited_with(
        "Введите ник пользователя (@username):")
    fake_state.set_state.assert_awaited_with(handlers.Form.waiting_username)


@pytest.mark.asyncio
async def test_process_fusername_and_no_balance(dummy_message):
    handlers.check_points.return_value = 0
    dummy_message.text = "@alice"
    fake_state = AsyncMock()
    await handlers.process_fusername(dummy_message, fake_state)
    dummy_message.answer.assert_awaited_with("❌ Недостаточно баллов: 0")
    fake_state.clear.assert_awaited()
