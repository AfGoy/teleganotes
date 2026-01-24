import asyncio
import logging
import sys
import hashlib

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from cryptography.fernet import Fernet

from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from db import init_db, add_note, get_list, del_data, edit_data, add_user, get_user, engine
from settings import TK, SECRET_KEY, ENCODE
from crypt import hash_password, verify_password

from crypt import cipher

class AddNoteFSM(StatesGroup):
    title = State()
    text = State()

class EditNoteFSM(StatesGroup):
    title = State()
    text = State()

class StartFSM(StatesGroup):
    name = State()
    password = State()

class GetListFSM(StatesGroup):
    password = State()

class DelNoteFSM(StatesGroup):
    title = State()

dp = Dispatcher(storage=MemoryStorage())



async def get_titles(owner):
    titles = []
    for i in await(get_list(owner)):
        titles.append(i[0])
    return titles

async def decode_list(list):
    list_decoded = []
    for coded in list:
        list_decoded.append(cipher.decrypt(coded).decode(ENCODE))
    return list_decoded

user_tg_id = None

async def start(message):
    pass

@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
        global user_tg_id
        user_tg_id = message.from_user.id
        kb = [
            [InlineKeyboardButton(text="🔒 Регистрация", callback_data="reg_btn")],
            [InlineKeyboardButton(text="👤 Профиль", callback_data="profile_btn")],
            [InlineKeyboardButton(text="➕ Добавить", callback_data="add_note_btn")],
            [InlineKeyboardButton(text="🗑 Удалить", callback_data="del_note_btn")],
            [InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_btn")],
            [InlineKeyboardButton(text="📄 Все заметки", callback_data="getlist_btn")],
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
        await message.reply(f"Здравствуйте, {message.from_user.username}, Этот бот создан для сохранения ваших заметок (а возможно и персональных данных 😉) в безопасности. Для ознакомления с командами пропишите /help \n\nАвтор: @soyaaa_l", reply_markup=keyboard)


@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery, state: FSMContext):
        if callback.data == "reg_btn":
            print(await get_user(user_tg_id))
            print(user_tg_id)
            if await get_user(user_tg_id) == None:
                await callback.message.answer(f"Введите имя, по которому можно к вам обращаться")
                await state.set_state(StartFSM.name)
            else:
                await callback.message.answer(f"Уже зарегестрированы")
                return
        elif callback.data == "profile_btn":
            user = await get_user(tg_id=user_tg_id)
            notes = await get_list(user_tg_id)
            await callback.message.answer(f"👤\nИмя - {user.name}\n\nКол-во заметок: {len(notes)}")
        elif callback.data == "add_note_btn":
            await state.set_state(AddNoteFSM.title)
            if not await get_user(user_tg_id):
                await callback.message.answer("У вас нет аккаунта, зарегестрируйтесь командой /start")
                await state.clear()
                return
            await callback.message.answer("✏️ Введите название заметки (для отмены: /cancel):")
        elif callback.data == "del_note_btn":
            await state.set_state(DelNoteFSM.title)
            await callback.message.answer("Введите название удаляемой заметки (для отмены: /cancel)")
        elif callback.data == "edit_btn":
            await state.set_state(EditNoteFSM.title)
            await callback.message.answer("Введите название заметки, которую вы хотите отредактировать (для отмены: /cancel):")
        elif callback.data == "getlist_btn":
                if await get_user(user_tg_id) == None:
                    await callback.message.answer("Зарегестрируйтесь")
                    return
                await state.set_state(GetListFSM.password)
                await callback.message.answer("Введите пароль 🔒")
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

@dp.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("❌ Нет активного действия для отмены.")
        return
    
    await state.clear()
    await message.answer("✅ Действие отменено.")

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
    await state.set_state(AddNoteFSM.text)
    await message.answer("📝 Теперь введите текст заметки:")


@dp.message(AddNoteFSM.text)
async def adddata_text(message: Message, state: FSMContext):
    if not message.text or not message.text.strip():
        await message.answer("Текст не может быть пустым. Введите ещё раз:")
        return

    data = await state.get_data()

    await add_note(owner=message.from_user.id, title=data["title"], title_hash=data["title_hash"], note_text=cipher.encrypt(message.text.encode(ENCODE)))

    await state.clear()
    await message.answer("✅ Заметка сохранена!")

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
    if await verify_password(message.text, password_hash):
        result = await(get_list(owner=message.from_user.id))
        if not result:
            await message.reply("У вас нет заметок")
            await state.clear()
            return
        for i in result:
            await message.answer(f"<b>{cipher.decrypt(i[0]).decode(ENCODE)}</b>: {cipher.decrypt(i[1]).decode(ENCODE)}")
            await state.clear()
    else:
        await message.answer("Ещё раз")
        return


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
    
    notes = await get_list(message.from_user.id)

    await del_data(owner=message.from_user.id, title_hash=hashlib.sha256(message.text.encode(ENCODE)).hexdigest())
    
    await state.clear()
    await message.answer("✅ Заметка удалена!")

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

@dp.message(Command("help"))
async def help_handler(message: Message):
    await message.answer("<b>/adddata</b> - Добавить заметку\n<b>/getlist</b> - Получить все свои заметки\n<b>/edit</b> - Перезаписать данные заметки\n<b>/delete</b> - Удалить заметку\n<b>/cancel</b> - Отменить диалог")

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

#TODO: Смена пороля, меню профиля, в старт месседже добавить маркап клавиатуру с функциями