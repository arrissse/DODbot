from flask import Flask, request
from aiogram import types
from bot import bot, dp, router
from database import db_manager
import asyncio
import logging
import newsletter
import users
import admin
import handlers
import admin_handlers
import newsletter
import add_admin
import merch
import quiz
import set_points


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
        data = request.get_data().decode("utf-8")
        update = types.Update.model_validate_json(data)
        await dp.feed_update(bot, update)
    except Exception as e:
        logging.exception("Ошибка при обработке обновления:")
        return "Ошибка", 500
    return "OK", 200


async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)
    await newsletter.start_immediate_newsletter()


async def on_shutdown(dispatcher):
    await bot.delete_webhook()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(on_startup())
    app.run(host="0.0.0.0", port=10181)
