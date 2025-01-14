import sys

import requests
from configuration.logger_setup import logger

# API ключ
api_key = "bb92ee43-b90e-4516-9483-63ae06351b64"

# URL для GraphQL
graphql_url = "https://api.fireflies.ai/graphql"

# Заголовки для запроса
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

# GraphQL запрос для получения данных транскрипта
query = """
query Transcript($transcriptId: String!) {
  transcript(id: $transcriptId) {
    id
    title
    summary {
      keywords
      action_items
      outline
      shorthand_bullet
      overview
      bullet_gist
      gist
      short_summary
    }
  }
}
"""


def get_transcript_summary(transcript_id):
    """
    Получает данные транскрипта (Summary: keywords, action_items, overview и т.д.).

    :param transcript_id: ID транскрипции
    :return: Словарь с данными Summary
    """
    # Переменные для GraphQL запроса
    variables = {"transcriptId": transcript_id}

    # Отправляем запрос
    response = requests.post(
        graphql_url,
        headers=headers,
        json={"query": query, "variables": variables},
        timeout=30,
    )

    # Обработка ответа
    if response.status_code == 200:
        data = response.json()
        if "data" in data and "transcript" in data["data"]:
            transcript = data["data"]["transcript"]
            return {
                "id": transcript["id"],
                "title": transcript["title"],
                "summary": transcript.get("summary", {}),
            }
        else:
            logger.error("Ошибка: данные не найдены.")
            logger.error(data)
    else:
        logger.error(f"Ошибка запроса: {response.status_code}")
        logger.error(response.text)


# Пример использования функции
if __name__ == "__main__":
    transcript_id = "sOCb1BMUWFEOO5oT"  # Укажите реальный ID транскрипции
    result = get_transcript_summary(transcript_id)
    logger.info(result.get("summary", {}).get("overview", None))
    logger.info(result.get("summary", {}).get("shorthand_bullet", None))
    # if result:
    #     logger.info(f"ID: {result['id']}")
    #     logger.info(f"Title: {result['title']}")
    #     logger.info("Summary:")
    #     for key, value in result["summary"].items():
    #         logger.info(f"{key}: {value}")
