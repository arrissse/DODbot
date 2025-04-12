from flask import Flask, request
from aiogram import types
from bot import bot, dp, router
import asyncio
import logging
from database import init_database
import newsletter
from . import users, admin, handler, admin_handlers, newsletter, add_admin, merch, quiz, set_points

dp.include_router(router)
WEBHOOK_URL = "https://fest.mipt.ru/your-webhook-path"

def register_all_handlers(dp):
    users.register(dp)
    admin.register(dp)
    handler.register(dp)
    admin_handlers.register(dp)
    newsletter.register(dp)
    add_admin.register(dp)
    merch.register(dp)
    quiz.register(dp)
    set_points.register(dp)

register_all_handlers(dp)

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
    await init_database()
    await newsletter.start_sending_newsletters()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(on_startup())
    app.run(host="0.0.0.0", port=10181)
