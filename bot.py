import telebot
from telebot import types

TOKEN = "7482828061:AAHZJLXCMmIbztAj49O5WpjKLs2zQC4yZEQ"
bot = telebot.TeleBot(TOKEN)

# Обработчик команды /start


@bot.message_handler(commands=["start"])
def start(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    item1 = types.KeyboardButton("📅 Расписание лекций")
    item2 = types.KeyboardButton("📍 Расположение физтех-школ")
    item3 = types.KeyboardButton("🗺 Карта")
    item4 = types.KeyboardButton("🎯 Квест")
    item5 = types.KeyboardButton("🎓 Квизы")
    markup.add(item1, item2, item3, item4, item5)
    bot.send_message(m.chat.id, "📌 Выберите действие:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "📅 Расписание лекций")
def send_schedule_photo(m):
    photo_url = "https://yandex-images.clstorage.net/VxuA95451/a5e90d24YZ1G/htu8jJO5XalGkgzMwk2De9ihpUvl8eXIZBeWhGLUOzEO6SqdSslL6GYzal-Hwfcer2FwS1zb9QnAztapHLTZU9ePeJgybBjd90dMTPIdoq4MkLSORbQ0bEHXUtTCBN5hDQ-dmgjajEsUgTiYQwS32691keo4zVOIoflCui4hXtQHe_9sN0qcymMh_jzSPNBcenCHTrZktSuglaNiYEKblo7sLiqra8yLFCIpCiA2Nfr9BURLWx4DHvPJAQpt0b1GJrvf_-bYvMkgsO3NMp2SvqtDBz01Rnc5YaUCcEGwmHYc7k846ZlMSAazaJmC59dLjEc1SFtuEz0xOAPJHjGc5kdav830aI6oQgEOLNFN419b4Fd91nbmGoEFMnITglgUbswvSOlYPdrHgwtoY7UEef42dRiI_vL8QDtiO8xxzGcG2Z78pFltuvMDDm8BTPPcqAHXj0X0pBrjlRBR83PLNi38LakK2n4I97BKeHCERYrN5vfpasyDDuH4QYh94g1UJynsPIUo_LphM23-ow-hrYngtJ9HhHR4cqcj49FCG6aP734bOkv_ynahKJhBxASa31cUadsus1xDO2AYDgFMFFYZPO9lSt6qg_EMzBBesm5qk-VcV0eGy0HlkMITYKg2Dc4NqGm4Hmk2gSlp8AcFGw6GRCo4veKsgmnCa2-j3xfF-X--59utKzJj_Y6w_uF8WvCkXGfnZdhxRaCRYdP79A6ejZgICO8aBkBIGYImRgmedDUZiU-xPJK7YCjd0W-1xqqPjCf737qhc34vck1DzjlRZR90JVcqkQWzgOLBOCRN3x2ZOuveS1UTOIjQJrYZjGQmWzt_sI6wm-AZHrCfV8fpvjw02-7oExIeTlB8oV654sSeRaeGSpMmgyHiY_rWvA_OuOp5rnlXUVob8jXlmO1mxZsLvIK8IFkBK-6yjsb3yN6eJ6qNurIBDZ1i_wJOmrLFjYXEpYrR9hDho"
    bot.send_photo(m.chat.id, photo_url,
                   caption="📅 Вот ваше расписание лекций!")

    # Если хотите отправить локальное фото:
    # with open("path/to/schedule.jpg", "rb") as photo:
    #     bot.send_photo(m.chat.id, photo, caption="📅 Вот ваше расписание лекций!")


@bot.message_handler(content_types=["text"])
def handle_text(message):
    responses = {
        "📍 Расположение физтех-школ": "📍 Физтех-школы расположены в кампусе.",
        "🗺 Карта": "🗺 Вот карта университета.",
        "🎯 Квест": "🎯 Пройдите квест и получите приз!",
        "🎓 Квизы": "🎓 Участвуйте в квизах!"
    }

    response = responses.get(message.text, "❌ Неизвестная команда.")
    bot.send_message(message.chat.id, response)


bot.polling(none_stop=True, interval=0)
