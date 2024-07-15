import telebot
from config import TOKEN

# Замените на ваш токен
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=["get_id"])
def send_user_id(message):
    user_id = message.from_user.id
    bot.reply_to(message, f"Your user ID: {user_id}")


# Запустите бота
bot.polling()
