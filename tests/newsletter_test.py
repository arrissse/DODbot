import asyncio
from unittest.mock import AsyncMock

import pytest
from aiogram.types import InlineKeyboardMarkup

from src.admin_handlers import newsletter


class DummyMessage:
    """Заглушка для aiogram Message, используемая в тестах."""

    def __init__(self, text, username="master", chat_id=42):
        """Инициализация тестового сообщения.

        Args:
            text: Текст сообщения
            username: Имя пользователя (по умолчанию 'master')
            chat_id: ID чата (по умолчанию 42)
        """
        self.text = text
        self.from_user = type("U", (), {"username": username})
        self.chat = type("C", (), {"id": chat_id})
        self.bot = AsyncMock()
        self.answer = AsyncMock()


class DummyCallback:
    """Заглушка для aiogram Message, используемая в тестах."""

    def __init__(self, data, message):
        """Инициализация callback.

        Args:
            data: иформация, переданная в callback
            message: сообщение, переданное в callback
        """
        self.data = data
        self.message = message
        self.answer = AsyncMock()


class DummyState:
    """Заглушка для aiogram CallbackQuery, используемая в тестах."""

    def __init__(self):
        self._data = {}
        self.set_state = AsyncMock()
        self.update_data = AsyncMock(
            side_effect=lambda **kw: self._data.update(kw))
        self.get_data = AsyncMock(side_effect=lambda: self._data)
        self.clear = AsyncMock()


@pytest.fixture(autouse=True)
def patch_db_and_users(monkeypatch):
    """
    Automatically patches database functions and user-related logic for all tests.

    Parameters:
        monkeypatch: Built-in pytest fixture for dynamic patching.

    Yields:
        None. Patches are applied for the duration of the test.
    """

    class DummyConn:
        async def execute(self, *args, **kwargs): pass
        async def commit(self): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
    monkeypatch.setattr(newsletter.db_manager,
                        "get_connection", lambda: DummyConn())

    monkeypatch.setattr(newsletter, "get_admin_by_username",
                        AsyncMock(return_value="@master"))
    monkeypatch.setattr(newsletter, "get_admin_level",
                        AsyncMock(return_value=0))

    monkeypatch.setattr(newsletter, "get_all_users", AsyncMock(return_value=[
        {"id": "10", "username": "alice"},
        {"id": "xyz", "username": "bob"},
    ]))

    monkeypatch.setattr(newsletter.bot, "send_message", AsyncMock())
    yield


@pytest.mark.asyncio
async def test_init_db_creates_table_and_logs(monkeypatch, caplog):
    caplog.set_level("INFO")
    await newsletter.init_db()
    assert "Таблица newsletter создана/проверена" in caplog.text


@pytest.mark.asyncio
async def test_add_newsletter_with_valid_time(monkeypatch, caplog):
    caplog.set_level("INFO")
    await newsletter.add_newsletter("Hello!", "2030-01-01 12:34")
    assert "Рассылка запланирована на 2030-01-01 12:34" in caplog.text


@pytest.mark.asyncio
async def test_add_newsletter_with_invalid_time(monkeypatch, caplog):
    caplog.set_level("ERROR")
    await newsletter.add_newsletter("Oops!", "bad-date")
    assert "Ошибка формата времени" in caplog.text


@pytest.mark.asyncio
async def test_handle_newsletter_permits_admin_and_sets_state():
    msg = DummyMessage("Отправить рассылку", username="master")
    state = DummyState()
    await newsletter.handle_newsletter(msg, state)
    msg.answer.assert_awaited_with("📝 Введите текст рассылки:")
    state.set_state.assert_awaited_with(
        newsletter.NewsletterStates.waiting_newsletter_text)


@pytest.mark.asyncio
async def test_handle_newsletter_denies_non_admin(monkeypatch):
    monkeypatch.setattr(newsletter, "get_admin_level",
                        AsyncMock(return_value=1))
    msg = DummyMessage("Отправить рассылку", username="other")
    state = DummyState()
    await newsletter.handle_newsletter(msg, state)
    msg.answer.assert_awaited_with("❌ Нет доступа!")
    state.set_state.assert_not_called()


@pytest.mark.asyncio
async def test_process_newsletter_text_prompts_time_and_updates_data():
    msg = DummyMessage("Hello everyone")
    state = DummyState()
    await newsletter.process_newsletter_text(msg, state)
    state.update_data.assert_awaited_with(text="Hello everyone")
    called = msg.answer.call_args.kwargs
    assert "⏰ Выберите время отправки:" in msg.answer.call_args.args[0]
    assert isinstance(called["reply_markup"], InlineKeyboardMarkup)


@pytest.mark.asyncio
async def test_handle_send_option_now(monkeypatch):
    cb = DummyCallback("send_now", DummyMessage("ignored"))
    state = DummyState()
    state._data["text"] = "Immediate!"
    await newsletter.handle_send_option(cb, state)
    cb.answer.assert_awaited_once()
    assert newsletter.bot.send_message.await_count == 1
    cb.message.answer.assert_awaited_with("✅ Рассылка начата!")


@pytest.mark.asyncio
async def test_handle_send_option_later_sets_state(monkeypatch):
    cb = DummyCallback("schedule_later", DummyMessage("ignored"))
    state = DummyState()
    state._data["text"] = "Later!"
    await newsletter.handle_send_option(cb, state)
    cb.answer.assert_awaited_once()
    cb.message.answer.assert_awaited_with(
        "📅 Введите дату и время в формате:\nYYYY-MM-DD HH:MM")
    state.set_state.assert_awaited_with(
        newsletter.NewsletterStates.waiting_custom_time)


@pytest.mark.asyncio
async def test_send_newsletter_logs_and_handles_invalid_id(caplog):
    caplog.set_level("ERROR")
    await newsletter.send_newsletter("Test")
    assert "Некорректный ID пользователя" in caplog.text
    assert newsletter.bot.send_message.await_count == 1


@pytest.mark.asyncio
async def test_process_custom_time_saves_and_clears_state(caplog):
    caplog.set_level("INFO")
    msg = DummyMessage("2031-12-31 23:59")
    state = DummyState()
    state._data["text"] = "Future news"
    await newsletter.process_custom_time(msg, state)
    assert "Рассылка запланирована на 2031-12-31 23:59!" in msg.answer.await_args.args[0]
    state.clear.assert_awaited()


@pytest.mark.asyncio
async def test_process_custom_time_bad_format_replies_error(state=None):
    msg = DummyMessage("not-a-date")
    state = DummyState()
    state._data["text"] = "Lost text"
    await newsletter.process_custom_time(msg, state)
    msg.answer.assert_awaited_with(
        "❌ Неверный формат времени! Используйте YYYY-MM-DD HH:MM")
    state.clear.assert_awaited()


@pytest.mark.asyncio
async def test_newsletter_scheduler_no_users(monkeypatch, caplog):
    monkeypatch.setattr(newsletter, "get_all_users",
                        AsyncMock(return_value=[]))

    class DummyConn2:
        async def execute(self, *args, **kwargs):
            class Cur:
                async def fetchall(self): return [(1, "msg")]
            return Cur()

        async def commit(self): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
    monkeypatch.setattr(newsletter.db_manager,
                        "get_connection", lambda: DummyConn2())
    caplog.set_level("WARNING")
    task = asyncio.create_task(newsletter.newsletter_scheduler(newsletter.bot))
    await asyncio.sleep(0.1)
    task.cancel()
    assert "Нет пользователей для рассылки." in caplog.text
