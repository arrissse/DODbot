from bot import bot, telebot
from flask import Flask, request, abort
import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError
import time
from telebot.apihelper import ApiTelegramException
import quiz
import set_points
import add_admin
import newsletter
import admin_handlers
import handlers
import logging
from threading import Lock

db_lock = Lock()

admin_handlers.create_price_table()

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

@app.route('/test')
def test():
    return "Test page"

@app.route('/your-webhook-path', methods=['POST'])
def webhook():
    print("Webhook received!")
    json_str = request.get_data(as_text=True)
    print(f"Raw data: {json_str}")
    if not json_str:
        return "No data received", 400

    try:
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return "Failed to process update", 500

    return "OK", 200


@app.route("/your-webhook-path", methods=["GET"])
def index():
    return "Flask server is running!", 200

@app.route("/", methods=["GET"])
def home():
    return "Flask server is running!", 200

def set_webhook_with_retry():
    retries = 5
    for _ in range(retries):
        try:
            bot.set_webhook(url="https://fest.mipt.ru/your-webhook-path")
            print("Webhook установлен успешно!")
            return
        except Exception as e:
            print(f"Ошибка при установке webhook: {e}")
            time.sleep(10)
    print("Не удалось установить webhook после нескольких попыток.")


if __name__ == '__main__':
    #bot.remove_webhook()
    try:
        bot.set_webhook(url="https://fest.mipt.ru/your-webhook-path")
    except ApiTelegramException as e:
        if e.result_json['error_code'] == 429:
            retry_after = e.result_json['parameters']['retry_after']
            print(f"Too many requests. Retrying after {retry_after} seconds...")
            time.sleep(1)
            bot.set_webhook(url="https://fest.mipt.ru/your-webhook-path")

    print(bot.get_webhook_info())

    

    app.run(host="0.0.0.0", port=10181, debug=True)
