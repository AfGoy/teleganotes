import asyncio
import logging
import sys
import hashlib
import json

from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, WebAppInfo
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from db import init_db, add_note, get_list, del_data, edit_data, add_user, get_user, update_note, engine
from settings import TK, ENCODE, WEBAPP_URL, GROQ_API_KEY, AI_URL, AI_GENERATE_ROUTER, JSON_PROMT_FILENAME
from crypt import verify_password, cipher
from states import *
from functions import get_titles, decode_list, get_payload_from_json
from client import Client

dp = Dispatcher(storage=MemoryStorage())
client_ai = Client(AI_URL, GROQ_API_KEY)


notes_ids = []
generated_text = ""

async def start(message, user_tg_id=None):
    user = await get_user(user_tg_id)
    if user:
        kb = [
            [InlineKeyboardButton(text="👤 Профиль", callback_data="profile_btn")],
            [InlineKeyboardButton(text="➕ Добавить", callback_data="add_note_btn")],
            [InlineKeyboardButton(text="🗑 Удалить", callback_data="del_note_btn")],
            [InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_btn")],
            [InlineKeyboardButton(text="📄 Все заметки", callback_data="getlist_btn")],
            [InlineKeyboardButton(text="❌ Очистить заметки из чата", callback_data="clear_btn")],
        ]
    else:
        kb = [[InlineKeyboardButton(text="🔒 Регистрация", callback_data="reg_btn")]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
    await message.reply(f"Здравствуйте, {message.from_user.username}, Этот бот создан для сохранения ваших заметок (а возможно и персональных данных 😉) в безопасности. Для ознакомления с командами пропишите /help \n\nАвтор: @soyaaa_l", reply_markup=keyboard)

@dp.message(CommandStart())
async def start_handler(message: Message):
    await start(message=message, user_tg_id=message.from_user.id)

@dp.callback_query(F.data.in_({
    "profile_btn",
    "add_note_btn",
    "del_note_btn",
    "edit_btn",
    "getlist_btn",
    "clear_btn",
    "reg_btn"
}))
async def callback_handler(callback: types.CallbackQuery, state: FSMContext):
    match callback.data: 
        case "reg_btn":
            if await get_user(callback.from_user.id) is None:
                await callback.message.answer("Введите имя, по которому можно к вам обращаться")
                await state.set_state(StartFSM.name)
            else:
                await callback.message.answer("Уже зарегистрированы")
                return

        case "profile_btn":
            user = await get_user(tg_id=callback.from_user.id)
            notes = await get_list(callback.from_user.id)
            await callback.message.answer(
                f"👤\nИмя - {user.name}\n\nКол-во заметок: {len(notes)}"
            )

        case "add_note_btn":
            await state.set_state(AddNoteFSM.title)
            if not await get_user(callback.from_user.id):
                await callback.message.answer(
                    "У вас нет аккаунта, зарегистрируйтесь командой /start"
                )
                await state.clear()
                return
            await callback.message.answer(
                "✏️ Введите название заметки (для отмены: /cancel):"
            )

        case "del_note_btn":
            await state.set_state(DelNoteFSM.title)
            await callback.message.answer(
                "Введите название удаляемой заметки (для отмены: /cancel)"
            )

        case "edit_btn":
            await state.set_state(EditNoteFSM.title)
            await callback.message.answer(
                "Введите название заметки, которую вы хотите отредактировать (для отмены: /cancel):"
            )

        case "getlist_btn":
            if await get_user(callback.from_user.id) is None:
                await callback.message.answer("Зарегистрируйтесь")
                return

            await state.set_state(GetListFSM.password)
            builder = ReplyKeyboardBuilder()
            builder.add(
                types.KeyboardButton(
                    text="🔐 Ввести пароль",
                    web_app=WebAppInfo(url=WEBAPP_URL)
                )
            )
            kb = builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
            await callback.message.answer("Введите пароль 🔒", reply_markup=kb)

        case "clear_btn":
            notes = await get_list(owner=callback.from_user.id)

            for note in notes:
                ids = note[3]

                if not ids:
                    continue

                for msg_id in ids:
                    if not isinstance(msg_id, int):
                        continue

                    try:
                        await callback.bot.delete_message(
                            chat_id=callback.message.chat.id,
                            message_id=msg_id
                        )
                    except Exception:
                        pass

        case _:
            pass
    await callback.answer() 

@dp.message(StartFSM.name)
async def start_password_handler(message: Message, state: FSMContext):
    if not message.text:
        await message.answer(f"Имя не может быть пустым!")
        return
    await state.update_data(name=message.text)
    await message.answer(f"Теперь введите свой НАДЁЖНЫЙ пароль")
    await state.set_state(StartFSM.password)

@dp.message(StartFSM.password)
async def final_start_handler(message: Message, state: FSMContext):
    if not message.text:
        await message.answer(f"Пароль не может быть пустым!")
        return
    
    data = await state.get_data()
    
    await state.clear()
    await message.answer(f"Успешно!")
    await add_user(tg_id=message.from_user.id, name=data["name"], password=message.text)
    await start(message=message, user_tg_id=message.from_user.id)

@dp.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("❌ Нет активного действия для отмены.")
        return
    
    await state.clear()
    await message.answer("✅ Действие отменено.")
    await start(message=message, user_tg_id=message.from_user.id)

@dp.message(Command("adddata"))
async def adddata_start(message: Message, state: FSMContext):
    await state.set_state(AddNoteFSM.title)
    if not await get_user(message.from_user.id):
        await message.answer("У вас нет аккаунта, зарегестрируйтесь командой /start")
        await state.clear()
        return
    await message.answer("✏️ Введите название заметки (для отмены: /cancel):")


@dp.message(AddNoteFSM.title)
async def adddata_title(message: Message, state: FSMContext):
    titles = await(get_titles(owner=message.from_user.id))
    if not message.text or not message.text.strip() or message.text.strip() in titles:
        await message.answer("Название не может быть пустым или повторяться. Введите ещё раз:")
        return

    await state.update_data(title=cipher.encrypt(message.text.encode(ENCODE)), title_hash=hashlib.sha256(message.text.encode(ENCODE)).hexdigest())
    kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Сгенерировать текст", callback_data="generate_text_btn")],
        [InlineKeyboardButton(text="✍️ Написать текст", callback_data="write_text_btn")]
    ]
    )
    await message.answer("📝 Выберите опцию:", reply_markup=kb)

@dp.callback_query(F.data.in_({
    "generate_text_btn",
    "write_text_btn",
}))
async def user_callback_handler(callback: types.CallbackQuery, state: FSMContext):
    match callback.data: 
        case "generate_text_btn":
            if state.get_state == "AddNoteFSM:title":
                await callback.message.answer("Введите промт для генерации текста:")
                await state.set_state(AddNoteFSM.ai_text)
            else:
                await callback.message.answer("Неверное состояние")
        case "write_text_btn":
            if state.get_state == "AddNoteFSM:title":
                await callback.message.answer("Введите текст заметки:")
                await state.set_state(AddNoteFSM.text)
            else:
                await callback.message.answer("Неверное состояние")
        case _:
            pass
    await callback.answer()

@dp.message(AddNoteFSM.text)
async def adddata_text(message: Message, state: FSMContext):
    if not message.text or not message.text.strip():
        await message.answer("Текст не может быть пустым. Введите ещё раз:")
        return

    data = await state.get_data()
    await add_note(owner=message.from_user.id, title=data["title"], title_hash=data["title_hash"], note_text=cipher.encrypt(message.text.encode(ENCODE)))
    await state.clear()
    await message.answer("✅ Заметка сохранена!")
    await start(message=message, user_tg_id=message.from_user.id)

@dp.message(AddNoteFSM.ai_text)
async def adddata_ai_text(message: Message, state: FSMContext):
    if not message.text or not message.text.strip():
        await message.answer("Промт не может быть пустым. Введите ещё раз:")
        return

    payload = get_payload_from_json(JSON_PROMT_FILENAME)
    payload["messages"][1]["content"] = message.text
    generated_text = await client_ai.post(AI_GENERATE_ROUTER, payload=payload)
    await state.update_data(generated_text=generated_text)
    kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="✅", callback_data="accept_btn")],
        [InlineKeyboardButton(text="❌", callback_data="decline_btn")]
    ]
    )
    await message.answer(f"Сгенерированный текст:\n\n{generated_text}\n\nЕсли вас устраивает сгенерированный текст, нажмите ✅, иначе ❌", reply_markup=kb)

@dp.callback_query(F.data.in_({
    "accept_btn",
    "decline_btn",
}))
async def ai_text_callback_handler(callback: types.CallbackQuery, state: FSMContext):
    match callback.data: 
        case "accept_btn":
            data = await state.get_data()
            await add_note(owner=callback.from_user.id, title=data["title"], title_hash=data["title_hash"], note_text=cipher.encrypt(data["generated_text"].encode(ENCODE)))
            await state.clear()
            await callback.message.answer("✅ Заметка сохранена!")

            await start(message=callback.message, user_tg_id=callback.from_user.id)
        case "decline_btn":
            await callback.message.answer("Введите промт для генерации текста:")
            await state.set_state(AddNoteFSM.ai_text)
        case _:
            pass

@dp.message(Command("getlist"))
async def get_all_password_enter(message: Message, state: FSMContext):
    if await get_user(message.from_user.id) == None:
        await message.answer("Зарегестрируйтесь")
        return
    await state.set_state(GetListFSM.password)

    await message.answer("Введите пароль 🔒")

@dp.message(GetListFSM.password)
async def get_all(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    password_hash = user.password_hash
    password = message.web_app_data.data
    if await verify_password(password, password_hash):
        result = await get_list(owner=message.from_user.id)
        if not result:
            await message.reply("У вас нет заметок")
            await state.clear()
            return
        for i in result:
            message_sended = await message.answer(f"<b>{cipher.decrypt(i[0]).decode(ENCODE)}</b>: {cipher.decrypt(i[1]).decode(ENCODE)}")
            await update_note(owner=message.from_user.id, title_hash=i[2], message_id=message_sended.message_id)
    else:
        await message.answer("Ещё раз")
        return
    await state.clear()
    await start(message=message, user_tg_id=message.from_user.id)


@dp.message(Command("delete"))
async def delete_handler_title_enter(message: Message, state: FSMContext):
    await state.set_state(DelNoteFSM.title)
    await message.reply("Введите название удаляемой заметки (для отмены: /cancel)")


@dp.message(DelNoteFSM.title)
async def delete_handler(message: Message, state: FSMContext):
    t = await(get_titles(owner=message.from_user.id))
    titles = await decode_list(t)
    if not message.text or message.text not in titles:
        await message.reply("Некоректное название")
        return

    await del_data(owner=message.from_user.id, title_hash=hashlib.sha256(message.text.encode(ENCODE)).hexdigest())
    await state.clear()
    await message.answer("✅ Заметка удалена!")
    await start(message=message, user_tg_id=message.from_user.id)

@dp.message(Command("edit"))
async def edit_handler(message: Message, state: FSMContext):
    await state.set_state(EditNoteFSM.title)
    await message.reply("Введите название заметки, которую вы хотите отредактировать (для отмены: /cancel):")

@dp.message(EditNoteFSM.title)
async def edit_handler_title(message: Message, state: FSMContext):
    t = await(get_titles(owner=message.from_user.id))
    titles = await decode_list(t)
    if not message.text or message.text not in titles:
        await message.reply("Некоректное название (Такой заметки нет или вы не ввели название)")
        return
    
    await state.update_data(title_hash=hashlib.sha256(message.text.encode(ENCODE)).hexdigest())
    await state.set_state(EditNoteFSM.text)
    await message.answer("Теперь введите новый текст этой заметки (ВНИМАНИЕ: СТАРЫЙ ТЕКСТ ПОЛНОСТЬЮ ЗАМЕНИТСЯ НА НОВЫЙ! Для отмены /cancel):")

@dp.message(EditNoteFSM.text)
async def edit_handler_text(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Текст не может быть пустым")
        return
    data = await state.get_data()

    await edit_data(owner=message.from_user.id, title_hash=data["title_hash"], new_text=cipher.encrypt(message.text.encode(ENCODE)))

    await state.clear()
    await message.answer("✅ Заметка изменена!")
    await start(message=message, user_tg_id=message.from_user.id)

@dp.message(Command("help"))
async def help_handler(message: Message):
    await message.answer("<b>/adddata</b> - Добавить заметку\n<b>/getlist</b> - Получить все свои заметки\n<b>/edit</b> - Перезаписать данные заметки\n<b>/delete</b> - Удалить заметку\n<b>/cancel</b> - Отменить диалог")
    await start(message=message, user_tg_id=message.from_user.id)

async def main() -> None:
    try:
        await init_db()
        bot = Bot(token=TK, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        await dp.start_polling(bot)
    finally:
        await engine.dispose()
    

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
