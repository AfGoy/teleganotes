import asyncio

from sqlalchemy import Column, Integer, String, select, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError


from settings import DB_URL
from models.quote import Quote

Base = declarative_base()

engine = create_async_engine(DB_URL)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    
async def add_quote(quote_text, owner):
    async with AsyncSessionLocal() as session:
        try:
            async with session.begin():
                owner = Quote
                quote = Quote(text=quote_text)
                session.add(quote)
            return "OK"
        
        except SQLAlchemyError as e:
            return f"Произошла ошибка при добавлении цитаты. {e}"
        

async def get_list(owner):
    async with AsyncSessionLocal() as session:
        try:
            async with session.begin():
                stmt = select(Quote.text).where(Quote.owner == owner)
                result = session.execute(stmt)
                texts = [row[0] for row in result.fetchall()]
            return texts
        
        except SQLAlchemyError as e:
            return f"Произошла ошибка базы данных. {e}"