from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from keyboards import main_keyboard

router = Router()


@router.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer("Привет! Выберите диапазон дат:", reply_markup=main_keyboard())


def register_handlers(dp):
    dp.include_router(router)
