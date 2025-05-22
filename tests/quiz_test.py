from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from src.user_handlers import quiz


@pytest_asyncio.fixture(autouse=True)
def patch_dependencies(monkeypatch):
    quiz.bot = MagicMock()
    quiz.bot.send_message = AsyncMock()

    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    mock_conn.cursor = AsyncMock(return_value=mock_cursor)
    mock_cursor.execute = AsyncMock(return_value=mock_cursor)
    mock_cursor.fetchall = AsyncMock(return_value=[])
    mock_cursor.fetchone = AsyncMock(return_value=None)

    class DummyConnCM:
        def __init__(self, conn):
            self._conn = conn

        async def __aenter__(self):
            return self._conn

        async def __aexit__(self, exc_type, exc, tb):
            pass

    dummy_cm = DummyConnCM(mock_conn)
    monkeypatch.setattr(quiz.db_manager, 'get_connection', lambda: dummy_cm)

    quiz._mock_cursor = mock_cursor

    quiz.update_quize_points = AsyncMock()
    quiz.check_quiz_points = AsyncMock(return_value=42)


@pytest.mark.asyncio
async def test_send_question_builds_keyboard_and_sends():
    answers = [(10, 'Answer A'), (20, 'Answer B'),
               (30, 'Answer C'), (40, 'Answer D')]
    mock_cursor = quiz._mock_cursor
    mock_cursor.fetchall.return_value = answers

    await quiz.send_question(
        chat_id=1234,
        user='testuser',
        question_id=1,
        question_number=3,
        quiz_id=99
    )

    quiz.bot.send_message.assert_awaited_once()
    chat_arg, text_arg = quiz.bot.send_message.call_args[0][:2]
    assert chat_arg == 1234
    assert '❔ Вопрос 3' in text_arg

    markup = quiz.bot.send_message.call_args[1]['reply_markup']
    texts = [btn.text for row in markup.inline_keyboard for btn in row]
    assert texts == ['А', 'Б', 'В', 'Г']

    for idx, row in enumerate(markup.inline_keyboard):
        btn = row[0]
        exp = f"answer:1:{answers[idx][0]}:testuser:99"
        assert btn.callback_data == exp


class DummyMessage:
    def __init__(self):
        self.chat = MagicMock(id=555)
        self.answer_text = None

    async def answer(self, text):
        self.answer_text = text


class DummyCallback:
    def __init__(self, data):
        self.data = data
        self.message = DummyMessage()
        self.answer = AsyncMock()


@pytest.mark.asyncio
async def test_check_answer_correct_with_next_question():
    mc = quiz._mock_cursor
    r1 = MagicMock()
    r1.fetchone = AsyncMock(return_value=(1,))
    r2 = MagicMock()
    r2.fetchone = AsyncMock(return_value=(2,))
    r3 = MagicMock()
    r3.fetchone = AsyncMock(return_value=(7,))
    r4 = MagicMock()
    r4.fetchone = AsyncMock(return_value=(3,))

    mc.execute.side_effect = [r1, r2, r3, r4]

    quiz.send_question = AsyncMock()
    # callback_data=f"answer:{question_id}:{ans_id}:{user}:{quiz_id}"
    cb = DummyCallback(data='answer:6:15:tester:42')
    await quiz.check_answer(cb)

    cb.answer.assert_awaited_once()
    quiz.update_quize_points.assert_awaited_once_with('tester', 42)
    quiz.send_question.assert_awaited_once_with(
        555, 'tester', 7, 3, 42
    )


@pytest.mark.asyncio
async def test_check_answer_incorrect_without_next_question():
    mc = quiz._mock_cursor
    r1 = MagicMock()
    r1.fetchone = AsyncMock(return_value=(0,))
    r2 = MagicMock()
    r2.fetchone = AsyncMock(return_value=(1,))
    r3 = MagicMock()
    r3.fetchone = AsyncMock(return_value=None)

    mc.execute.side_effect = [r1, r2, r3]

    cb = DummyCallback(data='answer:1:99:userX:7')

    await quiz.check_answer(cb)

    cb.answer.assert_awaited_once()
    quiz.update_quize_points.assert_not_awaited()
    assert cb.message.answer_text == 'Квиз завершён! Ваши баллы: 42'
