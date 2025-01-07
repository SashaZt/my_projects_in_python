import json

import requests

# Ваш API ключ
api_key = "bb92ee43-b90e-4516-9483-63ae06351b64"

# URL для получения всех транскрипций
transcripts_url = "https://api.fireflies.ai/graphql"

# Заголовки для запроса
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

# GraphQL запрос для получения всех транскрипций с их предложениями
query = """
query {
  transcripts {
    id
    title
    sentences {
      index
      speaker_name
      speaker_id
      text
      raw_text
      start_time
      end_time
      ai_filters {
        task
        pricing
        metric
        question
        date_and_time
        text_cleanup
        sentiment
      }
    }
  }
}
"""

# Отправляем запрос на получение всех транскрипций
response = requests.post(transcripts_url, headers=headers, json={"query": query})

if response.status_code == 200:
    result = response.json()
    if "data" in result and "transcripts" in result["data"]:
        for transcript in result["data"]["transcripts"]:
            print(
                f"Транскрипция ID: {transcript['id']}, Заголовок: {transcript['title']}"
            )
            if "sentences" in transcript:
                for sentence in transcript["sentences"]:
                    print(f"\tПредложение {sentence['index']}:")
                    print(
                        f"\t\tSpeaker: {sentence['speaker_name']} (ID: {sentence['speaker_id']})"
                    )
                    print(f"\t\tТекст: {sentence['text']}")
                    print(f"\t\tСырой текст: {sentence['raw_text']}")
                    print(
                        f"\t\tВремя начала: {sentence['start_time']}, Время окончания: {sentence['end_time']}"
                    )
                    if "ai_filters" in sentence:
                        print("\t\tAI Filters:")
                        for key, value in sentence["ai_filters"].items():
                            print(f"\t\t\t{key}: {value}")
            else:
                print("\tНет предложений в этой транскрипции.")
            print("-" * 50)  # Разделитель для читаемости
    else:
        print("Нет доступных транскрипций или ошибка в структуре ответа.")
else:
    print(f"Ошибка запроса: {response.status_code}")
    print(response.text)
