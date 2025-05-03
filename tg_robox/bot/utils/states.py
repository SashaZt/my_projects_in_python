from aiogram.fsm.state import State, StatesGroup


class BuyCardStates(StatesGroup):
    """Состояния для процесса покупки карты"""

    select_product = State()  # Выбор продукта
    confirm_payment = State()  # Подтверждение оплаты
    waiting_payment = State()  # Ожидание оплаты
