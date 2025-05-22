import asyncio
import logging
import tracemalloc

from aiogram import types
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web
from bot import bot, dp, router
from flask import Flask, request
from src.admin_handlers import (add_admin, merch_handlers, newsletter,
                                set_points)
from src.database import admin, merch, users
from src.database.base import db_manager
from src.user_handlers import handlers, quiz
from constants import WEBHOOK_URL, WEB_SERVER_HOST, WEB_SERVER_PORT

tracemalloc.start()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dp.include_router(router)

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    return "Flask + Aiogram бот работает!"


@app.route("/your-webhook-path", methods=["POST"])
async def webhook():
    try:
        data = request.get_data().decode("utf-8")
    except Exception as e:
        logger.exception("Ошибка при обработке обновления:")
        return "Ошибка", 500
    return "OK", 200


async def on_startup():
    """
    Хук запуска: инициализирует БД, таблицы и планировщик рассылки.
    """
    await bot.set_webhook(WEBHOOK_URL)
    await newsletter.init_db()
    await users.create_users_table()
    await admin.create_admins_table()
    await merch_handlers.create_price_table()
    await merch.create_merch_table()
    await quiz.create_quiz_table()
    logger.info("Таблица квизов создана")
    await admin.init_admins()

    asyncio.create_task(newsletter.newsletter_scheduler(bot))
    logger.info("Бот успешно запущен")


async def on_shutdown():
    await bot.delete_webhook()
    await dp.storage.close()


async def main():
    await on_startup()

    app = web.Application()
    handler = SimpleRequestHandler(dp, bot)
    handler.register(app, path="/your-webhook-path")

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, WEB_SERVER_HOST, WEB_SERVER_PORT)

    try:
        await site.start()
        logging.info("Сервер успешно запущен")
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()
        await on_shutdown()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен")
