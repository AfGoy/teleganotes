from aiogram.fsm.state import StatesGroup, State


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