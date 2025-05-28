from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from keyboards import reply as kb
from keyboards import inline as ikb
from config.logger import logger
import os

router = Router()


@router.message(F.text == "📞 Контактна інформація")
async def contact_info(message: Message):
    """Обработчик кнопки 'Контактна інформація'"""
    await message.answer(
        "📞 <b>Контактна інформація</b>\n\n"
        "📱 Номер телефону власника: +380683845703\n"
        "📱 ННомер служби підтримки клієнтів: +380683845703\n"
        "📧 Email: gamersqstore@gmail.com\n"
        "📑 Для ознайомлення з умовами оферти натисніть кнопку нижче:",
        reply_markup=ikb.get_offer_agreement_keyboard(),
    )


# @router.callback_query(F.data == "get_offer_pdf")
# async def send_offer_agreement(callback: CallbackQuery):
#     """Обработчик кнопки для отправки PDF с офертой"""
#     # Путь к файлу PDF в папке assets
#     pdf_path = "assets/documents/offer_agreement.pdf"

#     try:
#         # Проверяем существование файла
#         if os.path.exists(pdf_path):
#             # Отправляем файл как документ
#             await callback.message.answer_document(
#                 document=FSInputFile(pdf_path),
#                 caption="📄 Оферта публічного договору на продаж карт поповнення Roblox.",
#             )
#             await callback.answer("Документ відправлено!")
#         else:
#             logger.error(f"Файл не найден: {pdf_path}")
#             await callback.answer("На жаль, файл оферти не знайдено.")
#     except Exception as e:
#         logger.error(f"Ошибка при отправке PDF: {e}")
#         await callback.answer("На жаль, сталася помилка при відправці документу.")


# @router.callback_query(F.data == "back_to_menu")
# async def back_to_menu_from_contact(callback: CallbackQuery):
#     """Обработчик кнопки 'Назад' к главному меню"""
#     await callback.message.edit_text(
#         "📋 <b>Головне меню</b>\n\n" "Виберіть потрібний розділ:",
#         reply_markup=kb.get_main_menu_keyboard(),
#     )


# @router.message(F.text == "ℹ️ Про нас")
# async def about_us(message: Message):
#     """Обработчик кнопки 'Про нас'"""
#     await message.answer(
#         "ℹ️ <b>Про нас</b>\n\n"
#         "Ми — офіційний постачальник подарункових карток Roblox в Україні.\n\n"
#         "🔰 <b>Наші переваги:</b>\n"
#         "✅ Миттєва доставка кодів\n"
#         "✅ Гарантія працездатності кодів\n"
#         "✅ Офіційні карти поповнення Roblox\n"
#         "✅ Підтримка 24/7\n"
#         "✅ Зручні способи оплати\n\n"
#         "💯 Більше 1000 задоволених клієнтів щомісяця!\n\n"
#         "Дякуємо, що обрали нас для покупки карт поповнення Roblox!",
#         reply_markup=kb.get_main_menu_keyboard(),
#     )


# @router.message(F.text == "🛡 Гарантії")
# async def guarantees(message: Message):
#     """Обработчик кнопки 'Гарантії'"""
#     await message.answer(
#         "🛡 <b>Наші гарантії</b>\n\n"
#         "✅ <b>Офіційні карти</b>\n"
#         "Ми працюємо тільки з офіційними постачальниками карт поповнення Roblox.\n\n"
#         "✅ <b>Перевірка перед відправкою</b>\n"
#         "Кожен код перевіряється на працездатність перед відправкою клієнту.\n\n"
#         "✅ <b>Швидка заміна</b>\n"
#         "У рідкісному випадку, якщо код не спрацює, ми замінимо його протягом 24 годин.\n\n"
#         "✅ <b>Безпечна оплата</b>\n"
#         "Ми використовуємо захищені платіжні системи для безпеки ваших платежів.\n\n"
#         "❓ Якщо у вас виникли проблеми з кодом, зверніться до нашої підтримки.",
#         reply_markup=kb.get_main_menu_keyboard(),
#     )
