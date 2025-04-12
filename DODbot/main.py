from flask import Flask, request
from aiogram import types
from bot import bot, dp, router
from database import db_manager
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web
import asyncio
import logging
import newsletter
import users
import admin
import handlers
import admin_handlers
import add_admin
import merch
import quiz
import set_points
import tracemalloc

tracemalloc.start()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dp.include_router(router)
WEBHOOK_URL = "https://fest.mipt.ru/your-webhook-path"

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    return "Flask + Aiogram бот работает!"


@app.route("/your-webhook-path", methods=["POST"])
async def webhook():
    try:
        # Flask request.get_data() работает синхронно,
        # поэтому можно использовать его напрямую в async view
        data = request.get_data().decode("utf-8")
        update = types.Update.model_validate_json(data)
        asyncio.create_task(dp.feed_update(bot, update))
    except Exception as e:
        logger.exception("Ошибка при обработке обновления:")
        return "Ошибка", 500
    return "OK", 200


async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)
    await newsletter.init_db()
    await users.create_users_table()
    await admin.create_admins_table()
    await admin_handlers.create_price_table()
    await merch.create_merch_table()
    await quiz.create_quiz_table()
    await admin.init_admins()
    asyncio.create_task(newsletter.newsletter_scheduler())


async def on_shutdown():
    await bot.delete_webhook()
    await dp.storage.close()

WEBHOOK_URL = "https://fest.mipt.ru/your-webhook-path"
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = 10181

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
