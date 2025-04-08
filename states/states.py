from aiogram.fsm.state import State, StatesGroup

class ProductState(StatesGroup):
    """States for adding/editing products"""
    title = State()
    description = State()
    price = State()
    category = State()
    preview_image = State()
    file = State()
    available = State()

class AddBalanceState(StatesGroup):
    """States for adding balance to users"""
    username = State()
    amount = State()

class PaymentState(StatesGroup):
    """States for payment process"""
    select_amount = State()
    select_method = State()
    confirm = State()