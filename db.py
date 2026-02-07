from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from settings import DB_URL
from crypt import hash_password

from base import Base
from models.note import Note
from models.users import User

engine = create_async_engine(DB_URL)
AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def add_user(tg_id, name, password):
    async with AsyncSessionLocal() as session:
        try:
            async with session.begin():
                user = User(
                    tg_id=tg_id, name=name, password_hash=await hash_password(password)
                )
                session.add(user)
            return "OK"

        except SQLAlchemyError as e:
            return f"Произошла ошибка при добавлении текста. {e}"


async def get_user(tg_id):
    async with AsyncSessionLocal() as session:
        try:
            async with session.begin():
                stmt = select(User).where(User.tg_id == tg_id)
                result = await session.execute(stmt)
                return result.scalar_one_or_none()

        except SQLAlchemyError as e:
            return f"Произошла ошибка базы данных. {e}"


async def add_note(note_text, title, title_hash, owner):
    async with AsyncSessionLocal() as session:
        try:
            async with session.begin():
                note = Note(
                    owner=owner, title=title, text=note_text, title_hash=title_hash
                )
                session.add(note)
            return "OK"

        except SQLAlchemyError as e:
            return f"Произошла ошибка при добавлении текста. {e}"


async def update_note(title_hash, owner, message_id):
    async with AsyncSessionLocal() as session:
        try:
            async with session.begin():
                stmt = select(Note).where(
                    Note.owner == owner, Note.title_hash == title_hash
                )
                result = await session.execute(stmt)
                note = result.scalar_one_or_none()

                if not note:
                    return

                ids = note.ids_notes_in_chat or []
                ids.append(message_id)

                upd = (
                    update(Note).where(Note.id == note.id).values(ids_notes_in_chat=ids)
                )
                await session.execute(upd)

            return "✅ message_id добавлен"

        except SQLAlchemyError as e:
            return f"❌ Ошибка БД: {e}"


async def get_list(owner):
    async with AsyncSessionLocal() as session:
        try:
            stmt = select(
                Note.title, Note.text, Note.title_hash, Note.ids_notes_in_chat, Note.id
            ).where(Note.owner == owner)
            result = await session.execute(stmt)
            return result.all()

        except SQLAlchemyError as e:
            return f"Произошла ошибка базы данных. {e}"


async def del_data(owner, title_hash):
    async with AsyncSessionLocal() as session:
        try:
            async with session.begin():
                stmt = delete(Note).where(
                    Note.owner == owner, Note.title_hash == title_hash
                )
                await session.execute(stmt)
                await session.commit()
            return "OK"

        except SQLAlchemyError as e:
            return f"Произошла ошибка базы данных. {e}"


async def edit_data(owner, title_hash, new_text):
    async with AsyncSessionLocal() as session:
        try:
            async with session.begin():
                stmt = (
                    update(Note)
                    .where(Note.owner == owner, Note.title_hash == title_hash)
                    .values(text=new_text)
                )
                result = await session.execute(stmt)
            await session.commit()

            return f"✅ Изменено {result.rowcount} заметок"

        except SQLAlchemyError as e:
            return f"Произошла ошибка базы данных. {e}"


async def update_message_ids_in_note(note, msg_id: int):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            result = await session.execute(
                select(Note.ids_notes_in_chat).where(Note.id == note.id)
            )
            ids_list = result.scalar_one_or_none()
            print(ids_list)

            if not ids_list:
                return
            print(msg_id)
            ids_list.remove(msg_id)
            print(ids_list)

            await session.execute(
                update(Note)
                .where(Note.id == note.id)
                .values(ids_notes_in_chat=ids_list)
            )
            print(2)
            await session.commit()
