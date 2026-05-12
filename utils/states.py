from aiogram.fsm.state import State, StatesGroup


class SoloGameStates(StatesGroup):
    waiting_for_guess = State()


class PvPGameStates(StatesGroup):
    waiting_for_opponent = State()
    waiting_for_guess = State()
    waiting_for_join_code = State()