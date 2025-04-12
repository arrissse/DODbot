from aiogram import Bot, Dispatcher, Router
from aiogram.enums import ParseMode
from config import TOKEN

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
router = Router()