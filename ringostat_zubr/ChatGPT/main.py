import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# Путь к папкам
current_directory = Path.cwd()
data_directory = current_directory / "data"
files_directory = current_directory / "files"

data_directory.mkdir(parents=True, exist_ok=True)
files_directory.mkdir(parents=True, exist_ok=True)
output_csv_file = data_directory / "output.csv"
# Инициализация клиента OpenAI
env_path = os.path.join(os.getcwd(), "configuration", ".env")
load_dotenv(env_path)
api_key = os.getenv("API_KEY")
client = OpenAI(api_key=api_key)


# Функция для отправки текста из файла в GPT модель с инструкцией
def ask_openai_from_file():
    try:
        # Читаем содержимое текстового файла
        # with open(file_path, "r", encoding="utf-8") as file:
        #     text_content = file.read()
        text_content = "Алло, добрий день. Доброго дня. Торгова Марка Зубарда, слухаю вас. Я не можу миттє, це на той же фоні, в мене щось згалюсь. Коротше, присилайте мені стойкотел. А, зрозуміло, це ви Віталій Володимирович, я вас не опізнала. Ну добре, тоді, значить, обрали ми котел Прометея Економи з плитою 10-ти кіловатний, сталі 3 міліметри, з водонаповненими колесниками, да, з 13 900. Так? Добре. Добре. Ще тоді ще висотою, так, котел же сам по собі невеличкий, ви ж, мабуть, дивились на сайті, висотою 70 сантиметрів цього, ширина 30... Не треба ставкувати. Не треба. Добре. Все, тоді, дякую, що перезвонили, да, віддаю роботи, щоб на вівторок поставили на відправочку. Добре. Дякую вам. Гарного дня."
        question = (
            "Я даю тебе текст телефонных разговоров между менеджером и клиентом. Твоя задача — найти и выписать все вопросы, которые задавали клиенты."
            "Если какой-то вопрос повторяется в разных формулировках, объедини их в один пункт по смыслу."
            "Затем сформируй список из TOP-15 самых частых или наиболее важных вопросов. Если вопросов меньше 15 — укажи те, что есть."
            f"\n\n{text_content}"
        )

        # Создаем запрос к модели OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Или "gpt-4", в зависимости от задачи
            messages=[{"role": "user", "content": question}],
            max_tokens=150,
        )

        # Получаем ответ
        answer = response.choices[0].message.content.strip()
        return answer
    except Exception as e:
        return f"Ошибка при запросе к API: {e}"


if __name__ == "__main__":
    # txt_file = "txt_file.txt"
    answer = ask_openai_from_file()
