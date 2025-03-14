import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import requests
from auth import EbayAuth
from logger import logger
from models import Category, Item, SearchResult

from config import BASE_URL, DEFAULT_API_LIMIT, DEFAULT_MARKETPLACE_ID


class EbayApiClient:
    def __init__(self, auth: Optional[EbayAuth] = None):
        """Инициализация клиента API eBay"""
        self.auth = auth or EbayAuth()
        self.base_url = BASE_URL

    def _call_api(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        use_user_token: bool = False,
    ) -> Dict[str, Any]:
        """Базовый метод для вызова API eBay"""
        url = f"{self.base_url}/{endpoint}"

        if use_user_token:
            # Для методов, требующих User токен
            token_data = self.auth.user_token
            if not token_data:
                logger.error(
                    "User токен отсутствует. Необходима авторизация пользователя."
                )
                return {}

            # Проверка срока действия токена
            if (
                self.auth.user_token_expiry
                and datetime.now() > self.auth.user_token_expiry
            ):
                # Попытка обновления токена
                token_data = self.auth.refresh_user_token()
                if not token_data:
                    logger.error(
                        "Не удалось обновить User токен. Необходима повторная авторизация пользователя."
                    )
                    return {}
        else:
            # Для методов, требующих Application токен
            token_data = self.auth.get_application_token()
            if not token_data:
                logger.error("Не удалось получить Application токен.")
                return {}

        # Формирование заголовков
        request_headers = {
            "Authorization": f'Bearer {token_data["access_token"]}',
            "Content-Type": "application/json",
        }

        # Добавление пользовательских заголовков, если они предоставлены
        if headers:
            request_headers.update(headers)

        try:
            if method.upper() == "GET":
                response = requests.get(
                    url, headers=request_headers, params=params, timeout=30
                )
            elif method.upper() == "POST":
                response = requests.post(
                    url, headers=request_headers, json=data, params=params, timeout=30
                )
            elif method.upper() == "PUT":
                response = requests.put(
                    url, headers=request_headers, json=data, params=params, timeout=30
                )
            elif method.upper() == "DELETE":
                response = requests.delete(
                    url, headers=request_headers, params=params, timeout=30
                )
            else:
                logger.error(f"Неподдерживаемый HTTP метод: {method}")
                return {}

            response.raise_for_status()

            # Проверка на пустой ответ
            if not response.content:
                return {}

            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP ошибка при вызове API: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Ответ сервера: {e.response.text}")

            # Попытка обновления токена при ошибке авторизации
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                if use_user_token:
                    logger.info("Попытка обновления User токена...")
                    token_data = self.auth.refresh_user_token()
                    if token_data:
                        logger.info(
                            "User токен обновлен, повторная попытка вызова API..."
                        )
                        return self._call_api(
                            endpoint, method, params, data, headers, use_user_token
                        )
                else:
                    logger.info("Попытка получения нового Application токена...")
                    # Сброс токена и получение нового
                    self.auth.app_token = None
                    self.auth.app_token_expiry = None
                    token_data = self.auth.get_application_token()
                    if token_data:
                        logger.info(
                            "Application токен обновлен, повторная попытка вызова API..."
                        )
                        return self._call_api(
                            endpoint, method, params, data, headers, use_user_token
                        )

            return {}
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при вызове API: {e}")
            return {}

    # Методы для работы с API Taxonomy

    def get_default_category_tree_id(
        self, marketplace_id: str = DEFAULT_MARKETPLACE_ID
    ) -> str:
        """Получение ID дерева категорий по умолчанию для указанного маркетплейса"""
        endpoint = f"commerce/taxonomy/v1/get_default_category_tree_id"
        params = {"marketplace_id": marketplace_id}

        response = self._call_api(endpoint, params=params)
        return response.get("categoryTreeId", "")

    def get_category_tree(self, category_tree_id: str) -> Dict[str, Any]:
        """Получение полного дерева категорий"""
        endpoint = f"commerce/taxonomy/v1/category_tree/{category_tree_id}"
        return self._call_api(endpoint)

    def get_category_subtree(
        self, category_tree_id: str, category_id: str
    ) -> Dict[str, Any]:
        """Получение поддерева категорий для указанной категории"""
        endpoint = f"commerce/taxonomy/v1/category_tree/{category_tree_id}/get_category_subtree"
        params = {"category_id": category_id}
        return self._call_api(endpoint, params=params)

    def get_category_suggestions(
        self, query: str, category_tree_id: str
    ) -> List[Dict[str, Any]]:
        """Получение предложений категорий по поисковому запросу"""
        endpoint = f"commerce/taxonomy/v1/category_tree/{category_tree_id}/get_category_suggestions"
        params = {"q": query}
        response = self._call_api(endpoint, params=params)
        return response.get("categorySuggestions", [])

    # Методы для работы с API Browse

    def search_items(
        self,
        keywords: str,
        limit: int = DEFAULT_API_LIMIT,
        offset: int = 0,
        category_ids: Optional[List[str]] = None,
        filter_params: Optional[Dict[str, Any]] = None,
    ) -> SearchResult:
        """Поиск товаров по ключевым словам и фильтрам"""
        endpoint = "buy/browse/v1/item_summary/search"
        params = {
            "q": keywords,
            "limit": limit,
            "offset": offset,
        }

        # Добавление категорий к параметрам запроса
        if category_ids:
            params["category_ids"] = ",".join(category_ids)

        # Добавление дополнительных фильтров
        if filter_params:
            for key, value in filter_params.items():
                params[key] = value

        # Логирование полных параметров запроса
        logger.info(f"Поиск товаров с параметрами: {params}")

        response = self._call_api(endpoint, params=params)

        # Логирование структуры ответа
        if not response:
            logger.warning("Получен пустой ответ от API")
            return SearchResult(total=0, items=[])

        logger.info(f"Получен ответ с ключами: {list(response.keys())}")

        # Проверка ошибок
        if "errors" in response:
            logger.error(f"API вернуло ошибки: {response['errors']}")

        return SearchResult.from_dict(response)

    def get_item(self, item_id: str) -> Item:
        """Получение детальной информации о товаре по его ID"""
        endpoint = f"buy/browse/v1/item/{item_id}"
        response = self._call_api(endpoint)
        return Item.from_dict(response)

    def get_items_by_ids(self, item_ids: List[str]) -> List[Item]:
        """Получение информации о нескольких товарах по их ID"""
        endpoint = "buy/browse/v1/item"
        params = {"item_ids": ",".join(item_ids)}
        response = self._call_api(endpoint, params=params)
        items = []
        for item_data in response.get("items", []):
            items.append(Item.from_dict(item_data))
        return items
