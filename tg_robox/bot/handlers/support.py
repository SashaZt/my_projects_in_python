from aiogram import Router, F
from aiogram.types import Message
from keyboards import reply as kb

router = Router()


@router.message(F.text == "❓ Підтримка")
async def faq_support(message: Message):
    await message.answer(
        "❓ <b>Підтримка</b>\n\n"
        "Маєш питання чи щось не працює? Ми на зв’язку!\n"
        "Напиши нам у підтримку: @admin_username\n\n"
        "Перед зверненням переглянь поширені запитання нижче — можливо, відповідь уже тут:\n\n"
        "<b>Часті питання (FAQ):</b>\n"
        "1. <b>Як отримати код після оплати?</b>\n"
        "   — Після підтвердження оплати бот автоматично надішле код у чат.\n\n"
        "2. <b>Як активувати код Roblox?</b>\n"
        "   — Перейди на roblox.com/redeem, увійди в акаунт, введи код та натисни Redeem.\n\n"
        "3. <b>Що робити, якщо код не працює?</b>\n"
        "   — Переконайся, що ти не припустився помилки. Якщо код все одно не працює — звернись у підтримку.\n\n"
        "4. <b>Скільки часу чекати код після оплати?</b>\n"
        "   — Зазвичай код приходить миттєво. Якщо затримка — напиши в підтримку.",
        parse_mode="HTML",
        reply_markup=kb.get_main_menu_keyboard(),
    )
