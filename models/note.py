from sqlalchemy import Column, Integer, String, select, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from db import *

Base = declarative_base()

class Quote(Base):
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True)
    owner = Column(String)
    text = Column(String, nullable=False)

