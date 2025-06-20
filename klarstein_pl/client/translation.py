import json
import time
from typing import Dict, Optional, Tuple

import requests

from config import Config, logger, paths

config = Config.load()


class TranslationService:
    """Сервис для перевода текста через Google Translator API"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://google-translator9.p.rapidapi.com/v2"
        self.headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "google-translator9.p.rapidapi.com",
            "Content-Type": "application/json",
        }
        self.request_delay = 0.5  # Задержка между запросами (секунды)

    def _make_translation_request(
        self, text: str, target_language: str
    ) -> Optional[str]:
        """Выполняет запрос на перевод"""
        try:
            payload = {
                "q": text,
                "source": "pl",
                "target": target_language,
                "format": "text",
            }

            response = requests.post(
                self.base_url, headers=self.headers, json=payload, timeout=30
            )

            response.raise_for_status()

            result = response.json()

            # Извлекаем переведенный текст
            if "data" in result and "translations" in result["data"]:
                translations = result["data"]["translations"]
                if translations and len(translations) > 0:
                    translated_text = translations[0].get("translatedText", "")
                    return translated_text

            logger.error(f"Неожиданная структура ответа API: {result}")
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка HTTP запроса: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON ответа: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при переводе: {e}")
            return None

    def translate_polish_to_both(
        self, polish_text: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Переводит польский текст на русский и украинский

        Args:
            polish_text: Текст на польском языке

        Returns:
            Tuple[russian_text, ukrainian_text] - переводы или (None, None) при ошибке
        """
        try:
            if not polish_text or not polish_text.strip():
                return "", ""

            # logger.info(f"Переводим текст (длина: {len(polish_text)} символов)")

            # Переводим на русский
            russian_text = self._make_translation_request(polish_text, "ru")
            if russian_text is None:
                logger.error("Не удалось перевести на русский")
                return None, None

            # Задержка между запросами
            time.sleep(self.request_delay)

            # Переводим на украинский
            ukrainian_text = self._make_translation_request(polish_text, "uk")
            if ukrainian_text is None:
                logger.error("Не удалось перевести на украинский")
                return russian_text, None

            # logger.info("Перевод выполнен успешно")
            return russian_text, ukrainian_text

        except Exception as e:
            logger.error(f"Ошибка в translate_polish_to_both: {e}")
            return None, None

    def translate_batch_texts(self, texts: Dict[str, str]) -> Dict[str, Dict[str, str]]:
        """
        Переводит множественные тексты

        Args:
            texts: Словарь {key: polish_text}

        Returns:
            Словарь {key: {"ru": russian_text, "ua": ukrainian_text}}
        """
        results = {}
        total = len(texts)

        logger.info(f"Начинаем пакетный перевод {total} текстов")

        for i, (key, polish_text) in enumerate(texts.items(), 1):
            logger.info(f"Переводим {i}/{total}: {key}")

            try:
                russian_text, ukrainian_text = self.translate_polish_to_both(
                    polish_text
                )

                if russian_text is not None and ukrainian_text is not None:
                    results[key] = {"ru": russian_text, "ua": ukrainian_text}
                    logger.info(f"✓ Успешно переведен: {key}")
                else:
                    logger.error(f"✗ Ошибка перевода: {key}")
                    results[key] = {
                        "ru": polish_text,  # Fallback к оригинальному тексту
                        "ua": polish_text,
                    }

                # Дополнительная задержка между элементами
                if i < total:
                    time.sleep(self.request_delay)

            except Exception as e:
                logger.error(f"Ошибка при переводе {key}: {e}")
                results[key] = {"ru": polish_text, "ua": polish_text}

        success_count = sum(1 for r in results.values() if r["ru"] != r["ua"])
        logger.info(f"Пакетный перевод завершен. Успешно: {success_count}/{total}")

        return results

    def translate_product_data(self, product_data: Dict) -> Dict:
        """
        Переводит данные продукта (названия, описания, ключевые слова)

        Args:
            product_data: Данные продукта в YML формате

        Returns:
            Обновленные данные продукта с переводами
        """
        try:
            logger.info("Начинаем перевод данных продукта")

            # Переводим категории
            if "categories" in product_data:
                for category in product_data["categories"]:
                    name_pl = category.get("name_pl", "")
                    if name_pl:
                        russian_name, ukrainian_name = self.translate_polish_to_both(
                            name_pl
                        )
                        if russian_name and ukrainian_name:
                            category["name"] = russian_name
                            category["name_ua"] = ukrainian_name
                            logger.info(f"Переведена категория: {name_pl}")

            # Переводим товары
            if "offers" in product_data:
                for offer in product_data["offers"]:
                    # Переводим название товара
                    name_pl = offer.get("name_pl", "")
                    if name_pl:
                        russian_name, ukrainian_name = self.translate_polish_to_both(
                            name_pl
                        )
                        if russian_name and ukrainian_name:
                            offer["name"] = russian_name
                            offer["name_ua"] = ukrainian_name
                            logger.info(f"Переведено название товара")

                    # Переводим ключевые слова
                    keywords_pl = offer.get("keywords_pl", "")
                    if keywords_pl:
                        russian_keywords, ukrainian_keywords = (
                            self.translate_polish_to_both(keywords_pl)
                        )
                        if russian_keywords and ukrainian_keywords:
                            offer["keywords"] = russian_keywords
                            offer["keywords_ua"] = ukrainian_keywords
                            logger.info(f"Переведены ключевые слова")

                    # Переводим описание (готовый HTML)
                    description_pl = offer.get("description_pl", "")
                    if description_pl:
                        russian_desc, ukrainian_desc = self.translate_polish_to_both(
                            description_pl
                        )
                        if russian_desc and ukrainian_desc:
                            offer["description"] = russian_desc
                            offer["description_ua"] = ukrainian_desc
                            logger.info(f"Переведено описание товара")

            logger.info("Перевод данных продукта завершен")
            return product_data

        except Exception as e:
            logger.error(f"Ошибка при переводе данных продукта: {e}")
            return product_data


# Инициализация сервиса
API_KEY = config.client.translator_api_key
translator = TranslationService(API_KEY)


def translate_text(polish_text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Простая функция для перевода польского текста

    Args:
        polish_text: Текст на польском языке

    Returns:
        Tuple[russian_text, ukrainian_text]
    """
    return translator.translate_polish_to_both(polish_text)


def translate_yml_data(yml_data: Dict) -> Dict:
    """
    Переводит YML данные продукта

    Args:
        yml_data: Данные в YML формате

    Returns:
        Данные с переводами
    """
    return translator.translate_product_data(yml_data)


# # Пример использования
# if __name__ == "__main__":
#     # Тест простого перевода
#     test_text = "Kraftprotz, maszynka do mielenia mięsa, 700 W"
#     russian, ukrainian = translate_text(test_text)

#     print(f"Польский: {test_text}")
#     print(f"Русский: {russian}")
#     print(f"Украинский: {ukrainian}")

#     # Тест HTML перевода
#     html_text = """<ul class="list--no-style">
# <li><h3><strong>Po prostu lepszy smak: </strong>elektryczna maszynka do mięsa</h3></li>
# </ul>"""

#     russian_html, ukrainian_html = translate_text(html_text)
#     print(f"\nHTML перевод:")
#     print(f"Русский HTML: {russian_html}")
#     print(f"Украинский HTML: {ukrainian_html}")
