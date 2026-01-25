from sqlalchemy import Column, Integer, String, JSON
from base import Base

class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True)
    owner = Column(String)
    title = Column(String)
    text = Column(String, nullable=False)
    title_hash = Column(String)
    ids_notes_in_chat = Column(
        JSON,
        nullable=False,
        default=list
    )