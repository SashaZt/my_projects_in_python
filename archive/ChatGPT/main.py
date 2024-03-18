import openai
from config import API_KEY
import time
# Устанавливаем API ключ
openai.api_key = API_KEY


def ask_gpt3(prompt):
    try:
        # Отправляем запрос к модели
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        # Извлекаем ответ
        content = response['choices'][0]['message']['content'].strip()
        return content
    except openai.error.OpenAIError as e:
        print(f"Ошибка при выполнении запроса: {e}")
        return None


# Пример использования функции
start_time = time.time()  # Записываем начальное время
response = ask_gpt3("Напиши экспертную статью про автомобиль Audi A6 2016 года для автомобильного блога")
if response:
    print(response)
    end_time = time.time()  # Записываем конечное время
    elapsed_time = end_time - start_time  # Вычисляем разницу
    print(f"Время выполнения кода: {elapsed_time:.2f} секунд.")
else:
    print("Не удалось получить ответ.")
