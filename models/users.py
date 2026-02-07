from sqlalchemy import Column, Integer, String

from base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    tg_id = Column(String)
    name = Column(String)
    password_hash = Column(String)
