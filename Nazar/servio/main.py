"""
Клиент Servio для работы с бронированиями и номерами
Исправлена проблема с адресацией запросов
"""

import base64
import json
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from xml.dom import minidom

import requests

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s",
    handlers=[
        logging.FileHandler("servio_booking.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("servio_booking")

# Учетные данные для аутентификации
USERNAME = "Пац Денис"
PASSWORD = "пац888"

# URL сервиса
# URL сервиса
URL = "https://svc6.servio.support/8066/ServioExternalService"


class ServioBookingClient:
    """
    Клиент для работы с бронированиями Servio External Service
    """

    def __init__(self, url, username=None, password=None):
        """
        Инициализация клиента

        Args:
            url: URL сервиса
            username: Имя пользователя для аутентификации
            password: Пароль для аутентификации
        """
        self.url = url
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.verify = False  # Отключение проверки SSL-сертификатов
        logger.info(f"Инициализация клиента для {url}")

        # Загрузка WSDL для анализа сервиса
        self._load_wsdl()

        # Методы, связанные с бронированием
        self.booking_methods = [
            method
            for method in self.methods
            if "reservation" in method.lower()
            or "room" in method.lower()
            or "guest" in method.lower()
            or "client" in method.lower()
            or "hotel" in method.lower()
        ]

        logger.info(
            f"Найдено {len(self.booking_methods)} методов, связанных с бронированием: {', '.join(self.booking_methods)}"
        )

    def _load_wsdl(self):
        """Загрузка и анализ WSDL файла"""
        try:
            # Попробуем сначала использовать обычный URL с ?singleWsdl
            wsdl_url = f"{self.url}?singleWsdl"
            logger.info(f"Загрузка WSDL с URL: {wsdl_url}")
            response = self.session.get(wsdl_url)

            # Если возникла ошибка, попробуем другой формат URL для WSDL
            if response.status_code != 200:
                wsdl_url = f"{self.url}?wsdl"
                logger.info(f"Пробуем альтернативный URL для WSDL: {wsdl_url}")
                response = self.session.get(wsdl_url)

            if response.status_code != 200:
                logger.error(f"Ошибка при загрузке WSDL: {response.status_code}")
                raise Exception(f"Ошибка при загрузке WSDL: {response.status_code}")

            # Сохраняем WSDL
            self.wsdl_content = response.content

            # Извлекаем методы из WSDL
            self.methods = self._extract_methods_from_wsdl(self.wsdl_content)
            logger.info(
                f"Найдено {len(self.methods)} методов в WSDL: {', '.join(self.methods)}"
            )

            # Пытаемся определить правильное пространство имен для SOAP запросов
            self.soap_namespace = self._extract_soap_namespace(self.wsdl_content)
            logger.info(f"Используемое пространство имен: {self.soap_namespace}")

        except Exception as e:
            logger.error(f"Ошибка при загрузке WSDL: {e}")

            # Если не удалось загрузить WSDL, установим предопределенные методы и пространство имен
            logger.info("Используем предопределенный список методов")
            self.methods = [
                "GetReservationTypes",
                "GetRoomTypes",
                "GetRoomsModified",
                "GetHotels",
                "GetGuestsModified",
                "SearchClients",
                "AddClient",
                "UpdateClient",
                "UpdateGuest",
            ]
            self.soap_namespace = "http://tempuri.org/"

    def _extract_methods_from_wsdl(self, wsdl_content):
        """
        Извлечение доступных методов из WSDL

        Args:
            wsdl_content: Содержимое WSDL файла

        Returns:
            list: Список доступных методов
        """
        try:
            # Парсинг WSDL как XML
            root = ET.fromstring(wsdl_content)

            # Поиск всех операций
            methods = []

            # Регистрация используемых пространств имен
            namespaces = {
                "wsdl": "http://schemas.xmlsoap.org/wsdl/",
                "soap": "http://schemas.xmlsoap.org/wsdl/soap/",
                "xs": "http://www.w3.org/2001/XMLSchema",
            }

            # Поиск элементов <wsdl:operation>
            for operation in root.findall(".//wsdl:operation", namespaces):
                if "name" in operation.attrib:
                    methods.append(operation.attrib["name"])

            # Если не нашли операции, попробуем другой подход
            if not methods:
                logger.warning("Не найдены операции в WSDL. Пробуем другой подход.")
                # Поиск всех элементов с суффиксом Request или Response
                for element in root.findall(".//xs:element", namespaces):
                    if "name" in element.attrib:
                        name = element.attrib["name"]
                        if name.endswith("Request"):
                            method_name = name[:-7]  # Удаляем суффикс 'Request'
                            methods.append(method_name)

            return sorted(list(set(methods)))  # Удаляем дубликаты

        except Exception as e:
            logger.error(f"Ошибка при извлечении методов из WSDL: {e}")
            # Возвращаем стандартный набор методов в случае ошибки
            return [
                "GetReservationTypes",
                "GetRoomTypes",
                "GetRoomsModified",
                "GetHotels",
                "GetGuestsModified",
                "SearchClients",
            ]

    def _extract_soap_namespace(self, wsdl_content):
        """
        Извлечение правильного пространства имен для SOAP запросов

        Args:
            wsdl_content: Содержимое WSDL файла

        Returns:
            str: Пространство имен
        """
        try:
            # Парсинг WSDL как XML
            root = ET.fromstring(wsdl_content)

            # Регистрация используемых пространств имен
            namespaces = {
                "wsdl": "http://schemas.xmlsoap.org/wsdl/",
                "soap": "http://schemas.xmlsoap.org/wsdl/soap/",
            }

            # Пробуем найти targetNamespace в definitions
            if "targetNamespace" in root.attrib:
                return root.attrib["targetNamespace"]

            # Пробуем найти в soap:address
            for address in root.findall(".//soap:address", namespaces):
                if "location" in address.attrib:
                    location = address.attrib["location"]
                    # Извлекаем домен из URL
                    parts = location.split("/")
                    if len(parts) >= 3:
                        domain = parts[2]
                        return f"http://{domain}/"

            # Возвращаем значение по умолчанию
            return "http://tempuri.org/"

        except Exception as e:
            logger.error(f"Ошибка при извлечении пространства имен: {e}")
            return "http://tempuri.org/"

    def _create_soap_envelope(self, method_name, **params):
        """
        Создание SOAP-конверта для запроса

        Args:
            method_name: Название метода
            **params: Параметры метода

        Returns:
            str: SOAP-конверт
        """
        # Шаблон SOAP-конверта
        envelope_template = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
               xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <soap:Header>
    {header}
  </soap:Header>
  <soap:Body>
    <{method} xmlns="{namespace}">
      {params}
    </{method}>
  </soap:Body>
</soap:Envelope>"""

        # Создаем заголовок с авторизацией
        header = ""
        if self.username and self.password:
            header_template = """<AuthHeader xmlns="{namespace}">
      <Username>{username}</Username>
      <Password>{password}</Password>
    </AuthHeader>"""

            header = header_template.format(
                namespace=self.soap_namespace,
                username=self.username,
                password=self.password,
            )

        # Создаем параметры
        params_xml = ""
        for key, value in params.items():
            if value is None:
                params_xml += f'<{key} xsi:nil="true" />\n      '
            elif isinstance(value, (dict, list)):
                params_xml += f"<{key}>{self._dict_to_xml(value)}</{key}>\n      "
            else:
                params_xml += f"<{key}>{value}</{key}>\n      "

        # Собираем конверт
        envelope = envelope_template.format(
            header=header,
            method=method_name,
            namespace=self.soap_namespace,
            params=params_xml,
        )

        return envelope

    def _dict_to_xml(self, data):
        """
        Преобразование словаря или списка в XML

        Args:
            data: Словарь или список для преобразования

        Returns:
            str: XML-представление данных
        """
        if isinstance(data, dict):
            result = ""
            for key, value in data.items():
                if value is None:
                    result += f'<{key} xsi:nil="true" />'
                elif isinstance(value, (dict, list)):
                    result += f"<{key}>{self._dict_to_xml(value)}</{key}>"
                else:
                    result += f"<{key}>{value}</{key}>"
            return result
        elif isinstance(data, list):
            result = ""
            for item in data:
                if isinstance(item, dict):
                    # Предполагаем, что элементы списка имеют одинаковую структуру
                    tag = "Item"
                    result += f"<{tag}>{self._dict_to_xml(item)}</{tag}>"
                else:
                    result += f"<Item>{item}</Item>"
            return result
        else:
            return str(data)

    def _parse_soap_response(self, response_text, method_name):
        """
        Разбор ответа SOAP

        Args:
            response_text: Текст ответа
            method_name: Название метода

        Returns:
            dict: Результат в виде словаря
        """
        try:
            # Проверка на HTML ответ (ошибка 404 и т.п.)
            if response_text.strip().startswith(
                "<!DOCTYPE"
            ) or response_text.strip().startswith("<html"):
                return {"error": "HTTP Error", "details": response_text}

            # Парсинг XML-ответа
            root = ET.fromstring(response_text)

            # Определение пространств имен
            namespaces = {
                "soap": "http://schemas.xmlsoap.org/soap/envelope/",
                "xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "xsd": "http://www.w3.org/2001/XMLSchema",
            }

            # Проверка на наличие SOAP-ошибки
            fault = root.find(".//soap:Fault", namespaces)
            if fault is not None:
                fault_string = (
                    fault.find("./faultstring").text
                    if fault.find("./faultstring") is not None
                    else "Unknown fault"
                )
                fault_code = (
                    fault.find("./faultcode").text
                    if fault.find("./faultcode") is not None
                    else "Unknown code"
                )
                return {"error": f"SOAP Error: {fault_code}", "details": fault_string}

            # Поиск результата с разными вариантами пространства имен
            result_element = None

            # Пробуем разные варианты ответа
            response_name = f"{method_name}Response"
            result_name = f"{method_name}Result"

            # Поиск в любом пространстве имён
            for elem in root.findall(".//{*}" + response_name) or []:
                result_element = elem
                break

            if result_element is None:
                for elem in root.findall(".//{*}Body/*"):
                    if elem.tag.endswith(response_name):
                        result_element = elem
                        break

            if result_element is None:
                logger.warning(f"Не найден элемент {response_name} в ответе")
                return {"raw_response": response_text}

            # Преобразование XML в словарь
            result = self._xml_to_dict(result_element)

            # Если есть Result внутри Response, извлекаем его
            for key in result:
                if key.endswith(result_name):
                    return result[key]

            return result

        except ET.ParseError as e:
            logger.error(f"Ошибка при разборе XML ответа: {e}")
            return {
                "error": f"Ошибка при разборе XML ответа: {e}",
                "raw_response": response_text,
            }

    def _xml_to_dict(self, element):
        """
        Преобразование XML-элемента в словарь

        Args:
            element: XML-элемент

        Returns:
            dict: Словарь с данными из XML
        """
        result = {}

        # Обрабатываем атрибуты
        for key, value in element.attrib.items():
            result[f"@{key}"] = value

        # Обрабатываем вложенные элементы
        for child in element:
            tag = child.tag
            # Удаляем пространство имен из тега
            if "{" in tag and "}" in tag:
                tag = tag.split("}", 1)[1]

            # Рекурсивно преобразуем элемент
            child_dict = self._xml_to_dict(child)

            # Добавляем в результат
            if tag in result:
                # Если тег уже есть, преобразуем в список
                if not isinstance(result[tag], list):
                    result[tag] = [result[tag]]
                result[tag].append(child_dict)
            else:
                result[tag] = child_dict

        # Если есть только текст без дочерних элементов
        if element.text and element.text.strip() and not result:
            return element.text.strip()

        # Если есть текст и дочерние элементы
        if element.text and element.text.strip():
            result["#text"] = element.text.strip()

        return result

    def call(self, method_name, **params):
        """
        Вызов метода сервиса через SOAP

        Args:
            method_name: Название метода
            **params: Параметры метода

        Returns:
            dict: Результат вызова метода
        """
        try:
            logger.info(f"Вызов метода {method_name} с параметрами: {params}")

            # Создание SOAP-конверта
            soap_envelope = self._create_soap_envelope(method_name, **params)

            # Для отладки сохраняем запрос в файл
            with open(f"booking_request_{method_name}.xml", "w", encoding="utf-8") as f:
                # Форматируем XML для удобства чтения
                xml_dom = minidom.parseString(soap_envelope)
                formatted_xml = xml_dom.toprettyxml(indent="  ")
                f.write(formatted_xml)

            # Установка заголовков запроса
            headers = {
                "Content-Type": "text/xml; charset=utf-8",
                "SOAPAction": f'"{self.soap_namespace}{method_name}"',  # Добавлены кавычки
            }

            # Отправляем POST-запрос
            response = self.session.post(self.url, data=soap_envelope, headers=headers)

            # Проверка статуса ответа
            if response.status_code != 200:
                logger.error(
                    f"Ошибка HTTP при вызове {method_name}: {response.status_code}"
                )
                return {
                    "error": f"HTTP Error {response.status_code}",
                    "details": response.text,
                }

            # Для отладки сохраняем ответ в файл
            with open(
                f"booking_response_{method_name}.xml", "w", encoding="utf-8"
            ) as f:
                # Форматируем XML для удобства чтения
                try:
                    xml_dom = minidom.parseString(response.text)
                    formatted_xml = xml_dom.toprettyxml(indent="  ")
                    f.write(formatted_xml)
                except Exception:
                    f.write(response.text)

            # Разбор ответа SOAP
            result = self._parse_soap_response(response.text, method_name)

            return result

        except Exception as e:
            logger.error(f"Ошибка при вызове метода {method_name}: {e}")
            return {"error": str(e)}

    # =========== Методы для работы с бронированиями и отелями ===========

    def get_hotels(self):
        """
        Получение списка отелей

        Returns:
            dict: Информация об отелях
        """
        return self.call("GetHotels")

    def get_room_types(self, hotel_id=None):
        """
        Получение типов номеров

        Args:
            hotel_id: ID отеля (опционально)

        Returns:
            dict: Информация о типах номеров
        """
        params = {}
        if hotel_id:
            params["hotelID"] = hotel_id

        return self.call("GetRoomTypes", **params)

    def get_rooms_modified(self, from_date=None, to_date=None, hotel_id=None):
        """
        Получение информации об изменениях в номерах

        Args:
            from_date: Дата начала периода в формате ISO (опционально)
            to_date: Дата окончания периода в формате ISO (опционально)
            hotel_id: ID отеля (опционально)

        Returns:
            dict: Информация об измененных номерах
        """
        params = {}

        if from_date:
            if isinstance(from_date, datetime):
                params["from"] = from_date.isoformat()
            else:
                params["from"] = from_date

        if to_date:
            if isinstance(to_date, datetime):
                params["to"] = to_date.isoformat()
            else:
                params["to"] = to_date

        if hotel_id:
            params["hotelID"] = hotel_id

        return self.call("GetRoomsModified", **params)

    def get_reservation_types(self, hotel_id=None):
        """
        Получение типов бронирования

        Args:
            hotel_id: ID отеля (опционально)

        Returns:
            dict: Информация о типах бронирования
        """
        params = {}
        if hotel_id:
            params["hotelID"] = hotel_id

        return self.call("GetReservationTypes", **params)

    def get_guests_modified(self, from_date=None, to_date=None, hotel_id=None):
        """
        Получение информации об изменениях в гостях

        Args:
            from_date: Дата начала периода в формате ISO (опционально)
            to_date: Дата окончания периода в формате ISO (опционально)
            hotel_id: ID отеля (опционально)

        Returns:
            dict: Информация об измененных гостях
        """
        params = {}

        if from_date:
            if isinstance(from_date, datetime):
                params["from"] = from_date.isoformat()
            else:
                params["from"] = from_date

        if to_date:
            if isinstance(to_date, datetime):
                params["to"] = to_date.isoformat()
            else:
                params["to"] = to_date

        if hotel_id:
            params["hotelID"] = hotel_id

        return self.call("GetGuestsModified", **params)

    def search_clients(self, search_term):
        """
        Поиск клиентов

        Args:
            search_term: Строка поиска (имя, телефон, email и т.д.)

        Returns:
            dict: Результаты поиска клиентов
        """
        return self.call("SearchClients", searchString=search_term)

    def add_client(self, client_data):
        """
        Добавление нового клиента

        Args:
            client_data: Словарь с данными клиента

        Returns:
            dict: Результат операции
        """
        return self.call("AddClient", client=client_data)

    def update_client(self, client_data):
        """
        Обновление информации о клиенте

        Args:
            client_data: Словарь с данными клиента

        Returns:
            dict: Результат операции
        """
        return self.call("UpdateClient", client=client_data)

    def update_guest(self, guest_data):
        """
        Обновление информации о госте

        Args:
            guest_data: Словарь с данными гостя

        Returns:
            dict: Результат операции
        """
        return self.call("UpdateGuest", guest=guest_data)

    def accept_set(self, set_data):
        """
        Подтверждение набора данных

        Args:
            set_data: Данные для подтверждения

        Returns:
            dict: Результат операции
        """
        return self.call("AcceptSet", set=set_data)

    def test_booking_methods(self):
        """
        Тестирование методов бронирования без параметров

        Returns:
            dict: Результаты вызова методов
        """
        results = {}

        # Тестирование метода GetHotels
        logger.info("Тестирование метода GetHotels")
        hotels_result = self.get_hotels()
        results["GetHotels"] = hotels_result

        # Тестирование метода GetRoomTypes
        logger.info("Тестирование метода GetRoomTypes")
        room_types_result = self.get_room_types()
        results["GetRoomTypes"] = room_types_result

        # Другие методы без обязательных параметров
        methods_to_test = [
            "GetReservationTypes",
            "GetRoomsModified",
            "GetGuestsModified",
        ]

        for method in methods_to_test:
            if method in self.methods:
                logger.info(f"Тестирование метода {method}")
                try:
                    result = self.call(method)
                    results[method] = result
                except Exception as e:
                    logger.error(f"Ошибка при вызове метода {method}: {e}")
                    results[method] = {"error": str(e)}

        return results


# Пример использования
def main():
    """
    Основная функция для тестирования работы с бронированиями
    """
    try:
        logger.info(
            f"Запуск клиента Servio для бронирований с пользователем: {USERNAME}"
        )

        # Создание клиента
        client = ServioBookingClient(URL, USERNAME, PASSWORD)

        # Тестируем методы для работы с бронированиями
        results = client.test_booking_methods()

        # Сохраняем результаты в файл
        with open("booking_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info("Результаты сохранены в файл booking_results.json")

        # Выводим результаты
        for method, result in results.items():
            logger.info(f"\nМетод: {method}")
            if "error" in result:
                logger.error(f"Ошибка: {result['error']}")
            else:
                logger.info(f"Успешный результат: {result}")

    except Exception as e:
        logger.error(f"Ошибка при тестировании бронирований: {e}")
        raise


if __name__ == "__main__":
    main()
