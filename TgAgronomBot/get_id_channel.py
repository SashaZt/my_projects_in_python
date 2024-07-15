import telebot
from config import TOKEN

# Замените на ваш токен
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=["get_chat_id"])
def send_chat_id(message):
    chat_id = message.chat.id
    bot.reply_to(message, f"Chat ID: {chat_id}")


# Запустите бота
bot.polling()
