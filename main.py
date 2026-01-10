import asyncio
import logging
import sys
from random import choice, randint
from dotenv import load_dotenv
import os
from sqlalchemy import Column, Integer, String, select, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from settings import TK, ADMIN_ID, IDS_LIST, DB_URL, ADDQUOTE
from db import *


#TODO:
#db.py вынести настройки бд
#модельку в папку моделс


init_db()

dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer("Я реальный Тамерлан")

@dp.message(Command("addquote"))
async def quote_handler(message: Message):
    full_text = message.text
    command = ADDQUOTE
    if full_text.startswith(command):
        quote_text = full_text[len(command):].strip()
    else:
        quote_text = full_text.split(maxsplit=1)[1] if len(full_text.split()) > 1 else ""


    if not quote_text:
        await message.answer("Цитата не может быть пустой. Пожалуйста, введите текст цитаты после команды /addquote.")
        return

    add_quote(quote_text=quote_text)


@dp.message()
async def echo_handler(message: Message):
    num = randint(0, 100)
    if message.from_user.id in IDS_LIST and num == 67:
        await message.answer("Тамерлан успокойся!")

async def main() -> None:
    await init_db()

    bot = Bot(token=TK, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    try:
        await dp.start_polling(bot)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

#list цитат
#Импорт из файла
#Импорт из гс (питон модуль найти)