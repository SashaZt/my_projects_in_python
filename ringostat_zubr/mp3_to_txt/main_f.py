# Загрузка Аудио на сервер
import time

import requests
from configuration.logger_setup import logger

# Ваш API ключ
api_key = "bb92ee43-b90e-4516-9483-63ae06351b64"

# URL для загрузки аудиофайла и получения транскрипции
api_url = "https://api.fireflies.ai/graphql"

# Заголовки для запроса
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def upload_audio(file_link):

    # GraphQL запрос для загрузки аудио
    upload_query = """
    mutation UploadAudio($input: AudioUploadInput!) {
    uploadAudio(input: $input) {
        success
        title
        message
    }
    }
    """

    # Данные для запроса
    variables = {
        "input": {
            "url": file_link,
            "title": "Meeting Title",  # Вы можете изменить это на желаемое название встречи
        }
    }

    # Отправляем POST запрос для загрузки файла
    response = requests.post(
        api_url,
        headers=headers,
        json={"query": upload_query, "variables": variables},
    )

    if response.status_code == 200:
        result = response.json()
        if result["data"]["uploadAudio"]["success"]:
            print("Аудио успешно загружено.")
            print("Титул:", result["data"]["uploadAudio"]["title"])
            print("Сообщение:", result["data"]["uploadAudio"]["message"])

            # Теперь нужно получить transcript_id, когда аудио будет обработано
            get_transcript_query = """
            query GetTranscriptByTitle($title: String!) {
            transcripts(title: $title) {
                id
            }
            }
            """

            # Ждем, пока аудио не будет обработано
            while True:
                get_transcript_response = requests.post(
                    api_url,
                    headers=headers,
                    json={
                        "query": get_transcript_query,
                        "variables": {"title": "Meeting Title"},
                    },
                )

                if get_transcript_response.status_code == 200:
                    get_transcript_result = get_transcript_response.json()
                    if get_transcript_result["data"]["transcripts"]:
                        transcript_id = get_transcript_result["data"]["transcripts"][0][
                            "id"
                        ]
                        logger.info(transcript_id)
                        return transcript_id
                    else:
                        logger.warning("Ожидание обработки аудио...")
                        time.sleep(10)  # Ждем 10 секунд перед следующим запросом
                else:
                    logger.error(
                        f"Ошибка при получении transcript_id: {get_transcript_response.status_code}"
                    )
                    logger.error(get_transcript_response.text)
                    return None
        else:
            logger.error(
                "Ошибка при загрузке аудио:", result["data"]["uploadAudio"]["message"]
            )
    else:
        logger.error(f"Ошибка при загрузке: {response.status_code}")
        logger.error(response.text)


def get_transcrip():
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

    # Отправка запроса
    response = requests.post(api_url, headers=headers, json={"query": query_transcript})

    # Обработка ответа
    if response.status_code == 200:
        data = response.json()
        if "data" in data and "transcripts" in data["data"]:
            for transcript in data["data"]["transcripts"]:
                transcript_id = transcript["id"]
                # Сбор всех предложений в одну строку
                full_text = " ".join(
                    sentence["text"] for sentence in transcript.get("sentences", [])
                )
                logger.info(full_text)
        else:
            logger.error("Нет данных.")
    else:
        logger.error(f"Ошибка: {response.status_code}")
        logger.error(response.text)
