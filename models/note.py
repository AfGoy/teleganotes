from sqlalchemy import Column, Integer, String, select, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from base import Base

class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True)
    owner = Column(String)
    title = Column(String)
    text = Column(String, nullable=False)
    title_hash = Column(String)