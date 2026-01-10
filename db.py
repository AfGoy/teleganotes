import asyncio

from sqlalchemy import Column, Integer, String, select, func, update, delete
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base

from settings import DB_URL

from base import Base
from models.note import Note

engine = create_async_engine(DB_URL)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    
async def add_note(note_text, title, owner):
    async with AsyncSessionLocal() as session:
        try:
            async with session.begin():
                note = Note(owner=owner, title=title, text=note_text)
                session.add(note)
            return "OK"
        
        except SQLAlchemyError as e:
            return f"Произошла ошибка при добавлении текста. {e}"
        

async def get_list(owner):
    async with AsyncSessionLocal() as session:
        try:
            stmt = select(Note.title, Note.text).where(Note.owner == owner)
            result = await session.execute(stmt)
            return result.all()

        except SQLAlchemyError as e:
            return f"Произошла ошибка базы данных. {e}"
        
async def del_data(owner, title):
        async with AsyncSessionLocal() as session:
            try:
                async with session.begin():  
                    stmt = delete(Note).where(Note.owner == owner, Note.title == title)
                    result = await session.execute(stmt)
                    await session.commit()  
                return "OK"
                
            except SQLAlchemyError as e:
                return f"Произошла ошибка базы данных. {e}"
        
async def edit_data(owner, title, new_text):
        async with AsyncSessionLocal() as session:
            try:
                async with session.begin():
                    stmt = (update(Note).where(Note.owner == owner, Note.title == title).values(text=new_text))
                    result = await session.execute(stmt)
                await session.commit()

                return f"✅ Изменено {result.rowcount} заметок"
                
            except SQLAlchemyError as e:
                return f"Произошла ошибка базы данных. {e}"