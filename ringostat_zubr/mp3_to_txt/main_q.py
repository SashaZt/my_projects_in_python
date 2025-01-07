# Получение траскрибации
import requests
from configuration.logger_setup import logger

# Ваш API ключ
api_key = "bb92ee43-b90e-4516-9483-63ae06351b64"

# URL для GraphQL
graphql_url = "https://api.fireflies.ai/graphql"

# Заголовки для запроса
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def get_transcrip(transcript_id):
    # GraphQL запрос для получения предложений
    query_transcript = """
    query {
    transcripts {
        id
        title
        sentences {
        text
        raw_text
        }
    }
    }
    """
    # Данные для запроса
    variables = {"transcriptId": transcript_id}
    # Отправка запроса
    response = requests.post(
        graphql_url,
        headers=headers,
        json={"query": query_transcript, "variables": variables},
    )

    # Обработка ответа
    if response.status_code == 200:
        data = response.json()
        if "data" in data and "transcripts" in data["data"]:
            for transcript in data["data"]["transcripts"]:
                transcript_id = transcript["id"]
                logger.info(transcript_id)
                # Сбор всех предложений в одну строку
                full_text = " ".join(
                    sentence["text"] for sentence in transcript.get("sentences", [])
                )
                return full_text
            logger.error("Нет данных.")
    else:
        logger.error(f"Ошибка: {response.status_code}")
        logger.error(response.text)


if __name__ == "__main__":
    get_transcrip("G6P6JOQS1Q8o99mo")
