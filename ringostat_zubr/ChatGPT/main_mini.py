# import os
# from pathlib import Path
# from dotenv import load_dotenv
# from openai import OpenAI

# # Инициализация OpenAI
# env_path = os.path.join(os.getcwd(), "configuration", ".env")
# load_dotenv(env_path)
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# client = OpenAI()


# # Проверка API-ключа
# if not OPENAI_API_KEY:
#     raise ValueError("API ключ не найден. Проверьте файл .env.")

# def ask_openai_from_file(text_content):
#     try:
#         question = (
#             "Я даю тебе тексты  75 телефонных разговоров между менеджером и клиентом. Твоя задача — найти и выписать все вопросы, которые задавали клиенты."
#             "Если какой-то вопрос повторяется в разных формулировках, объедини их в один пункт по смыслу."
#             "Затем сформируй список из TOP-15 самых частых или наиболее важных вопросов. Если вопросов меньше 15 — укажи те, что есть."
#             f"\n\n{text_content}"
#         )

#         # Запрос к OpenAI
#         response = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {"role": "system", "content": "You are a helpful assistant."},
#                 {"role": "user", "content": question}
#             ],
#             max_tokens=150,
#         )

#         print(response.choices[0].message)
#         return response.choices[0].message["content"].strip()
#     except Exception as e:
#         return f"Ошибка при запросе к API: {e}"

    

#     file_path = "conversations.txt"  # Укажите путь к вашему .txt файлу
#     text_content = read_file(file_path)  # Чтение текста из файла
#     print(text_content)

import os
import asyncio
from openai import AsyncOpenAI
from configuration.logger_setup import logger
from dotenv import load_dotenv

env_path = os.path.join(os.getcwd(), "configuration", ".env")
load_dotenv(env_path)
# Инициализация клиента
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Асинхронный вызов
async def main(text_content_conversation, text_content_question):
    question = (
            f"{text_content_question}"
            f"\n\n{text_content_conversation}"
        )
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": question}
        ]
    )
    # Извлечение данных
    message = response.choices[0].message.content
    completion_tokens = response.usage.completion_tokens
    prompt_tokens = response.usage.prompt_tokens
    total_tokens = response.usage.total_tokens

    # Запись данных в файлы
    write_to_file("response.txt", str(response))  # Полный response
    write_to_file("message.txt", message)        # Сообщение
    write_to_file("completion_tokens.txt", str(completion_tokens))  # Токены генерации
    write_to_file("prompt_tokens.txt", str(prompt_tokens))          # Токены запроса
    write_to_file("total_tokens.txt", str(total_tokens))            # Общее количество токенов
    logger.info(response)
    logger.info(message)
    logger.info(completion_tokens)
    logger.info(total_tokens)
# Функция для загрузки текста из файла
def read_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()
# Функция для записи данных в файл
def write_to_file(file_name, content):
    with open(file_name, "w", encoding="utf-8") as file:
        file.write(content)
if __name__ == "__main__":
    file_path_conversation = "conversations.txt"  # Укажите путь к вашему .txt файлу
    file_path_question = "question.txt"  # Укажите путь к вашему .txt файлу
    text_content_conversation = read_file(file_path_conversation)  # Чтение текста из файла
    text_content_question = read_file(file_path_question)  # Чтение текста из файла
    # Запуск асинхронного вызова
    asyncio.run(main(text_content_conversation, text_content_question))
