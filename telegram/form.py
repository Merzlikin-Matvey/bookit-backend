from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup


class AccessTokenForm(StatesGroup):
    token = State()