import logging
from typing import Any, Dict, List, Optional, Union

import zeep


class KazPostClient:
    """
    Клиент для работы с API KazPost для создания ТТН накладных
    """

    def __init__(
        self,
        key: str,
        wsdl_url: str = "http://rates.kazpost.kz/postratesws/postratesws.wsdl",
    ):
        """
        Инициализация клиента

        :param key: Идентификационный ключ клиента (32 символов)
        :param wsdl_url: URL для WSDL файла сервиса
        """
        self.key = key
        self.wsdl_url = wsdl_url
        self.client = self._create_client()

    def _create_client(self) -> zeep.Client:
        """Создание SOAP клиента"""
        # Включаем логирование для отладки (можно закомментировать в продакшене)
        logging.basicConfig(level=logging.INFO)
        logging.getLogger("zeep").setLevel(logging.DEBUG)

        # Создаем клиент
        return zeep.Client(wsdl=self.wsdl_url)

    def create_parcel_barcode(
        self,
        # Информация о получателе
        rcpn_iin: Optional[str] = None,
        rcpn_name: str = "",
        rcpn_phone: str = "",
        rcpn_email: Optional[str] = None,
        rcpn_country: Optional[str] = "Казахстан",
        rcpn_index: str = "",
        rcpn_city: Optional[str] = "",
        rcpn_district: Optional[str] = None,
        rcpn_street: str = "",
        rcpn_house: str = "",
        # Информация об отправителе
        sndr_bin: str = "",
        sndr_name: Optional[str] = "",
        sndr_phone: Optional[str] = "",
        sndr_email: Optional[str] = None,
        sndr_country: Optional[str] = "Казахстан",
        sndr_index: str = "",
        sndr_city: Optional[str] = "",
        sndr_district: Optional[str] = None,
        sndr_street: Optional[str] = "",
        sndr_house: Optional[str] = "",
        # Информация о посылке
        weight: Optional[str] = None,
        declared_value: Optional[str] = None,
        cash_on_delivery: Optional[str] = None,
        delivery_sum: Optional[str] = None,
        product_code: str = "",
        marks: Optional[List[str]] = None,
        add_info: Optional[List[str]] = None,
        part_num: Optional[str] = None,
        envelope_size: Optional[str] = None,
        send_method: str = "",
        mail_ctg: str = "",
        barcode: Optional[str] = None,
        order_num: Optional[str] = None,
        mail_count: Optional[str] = None,
        pickup: Optional[str] = None,
        npi: Optional[str] = None,
        dea_number: Optional[str] = None,
        dea_depcode: Optional[str] = None,
        # Дополнительные поля
        f1: Optional[str] = None,
        f2: Optional[str] = None,
        f3: Optional[str] = None,
        f4: Optional[str] = None,
        f5: Optional[str] = None,
        f6: Optional[str] = None,
        f7: Optional[str] = None,
        f8: Optional[str] = None,
        f9: Optional[str] = None,
        f10: Optional[str] = None,
        f11: Optional[str] = None,
        f12: Optional[str] = None,
        f13: Optional[str] = None,
        f14: Optional[str] = None,
        f15: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Создание ТТН накладной и получение трек-номера

        :return: Словарь с ответом от сервера
        """
        # Создаем объект AddrInfo с данными
        addr_info = {
            # Информация о получателе
            "RcpnIIN": rcpn_iin,
            "RcpnName": rcpn_name,
            "RcpnPhone": rcpn_phone,
            "RcpnEmail": rcpn_email,
            "RcpnCountry": rcpn_country,
            "RcpnIndex": rcpn_index,
            "RcpnCity": rcpn_city,
            "RcpnDistrict": rcpn_district,
            "RcpnStreet": rcpn_street,
            "RcpnHouse": rcpn_house,
            # Информация об отправителе
            "SndrBIN": sndr_bin,
            "SndrName": sndr_name,
            "SndrPhone": sndr_phone,
            "SndrEmail": sndr_email,
            "SndrCountry": sndr_country,
            "SndrIndex": sndr_index,
            "SndrCity": sndr_city,
            "SndrDistrict": sndr_district,
            "SndrStreet": sndr_street,
            "SndrHouse": sndr_house,
            # Информация о посылке
            "Weight": weight,
            "DeclaredValue": declared_value,
            "CashOnDelivery": cash_on_delivery,
            "DeliverySum": delivery_sum,
            "ProductCode": product_code,
            "SendMethod": send_method,
            "MailCtg": mail_ctg,
            "Barcode": barcode,
            "OrderNum": order_num,
            "MailCount": mail_count,
            "Pickup": pickup,
            "NPI": npi,
            "DEA_NUMBER": dea_number,
            "DEA_DEPCODE": dea_depcode,
            # Дополнительные поля
            "F1": f1,
            "F2": f2,
            "F3": f3,
            "F4": f4,
            "F5": f5,
            "F6": f6,
            "F7": f7,
            "F8": f8,
            "F9": f9,
            "F10": f10,
            "F11": f11,
            "F12": f12,
            "F13": f13,
            "F14": f14,
            "F15": f15,
        }

        # Добавляем отметки, если они предоставлены
        if marks:
            addr_info["Marks"] = {"Mark": marks}

        # Добавляем доп. информацию, если она предоставлена
        if add_info:
            addr_info["AddInfo"] = {"Field": add_info}

        # Добавляем размер конверта, если он предоставлен
        if envelope_size:
            addr_info["EnvelopeSize"] = envelope_size

        # Убираем None значения из словаря
        addr_info = {k: v for k, v in addr_info.items() if v is not None}

        # Создаем запрос
        request_data = {"Key": self.key, "AddrInfo": addr_info}

        try:
            # Отправляем запрос
            response = self.client.service.GetParcelBarcode(**request_data)
            return self._process_response(response)
        except Exception as e:
            return {
                "ResponseCode": "ERROR",
                "ResponseText": f"Ошибка при отправке запроса: {str(e)}",
                "Barcode": None,
                "Barcodes": None,
                "ResponseGenTime": None,
            }

    def _process_response(self, response) -> Dict[str, Any]:
        """Обработка ответа от сервера"""
        # Преобразуем ответ zeep в словарь Python
        response_dict = zeep.helpers.serialize_object(response)
        return response_dict


# Пример использования
if __name__ == "__main__":
    # Ваш ключ API из профиля на post.kz
    API_KEY = "EMKWG7x5dSrCowxnKd1adBItLi0lcwkR"  # Замените на свой ключ

    # Создаем клиент
    client = KazPostClient(key=API_KEY)

    # Пример создания ТТН для посылки
    result = client.create_parcel_barcode(
        # Информация о получателе
        rcpn_iin="123456789012",
        rcpn_name="ФИО получателя",
        rcpn_phone="77010000000",
        rcpn_email="test@test.com",
        rcpn_country="Казахстан",
        rcpn_index="010000",
        rcpn_city="Город",
        rcpn_district="Район",
        rcpn_street="Улица",
        rcpn_house="12",
        # Информация об отправителе
        sndr_bin="098765432121",
        sndr_name="Компания",
        sndr_phone="77010000000",
        sndr_email="company@company.com",
        sndr_country="Казахстан",
        sndr_index="050000",
        sndr_city="Город",
        sndr_district="Район",
        sndr_street="Улица",
        sndr_house="25",
        # Информация о посылке
        weight="1.55",
        declared_value="15000",
        cash_on_delivery="15000",
        product_code="P104",
        marks=["returnAfter"],
        send_method="2",
        mail_ctg="4",
        order_num="123456789",
        mail_count="1",
        dea_number="537868654454000542",
        dea_depcode="279900",
    )

    print("Результат запроса:")
    print(f"Код ответа: {result.get('ResponseCode')}")
    print(f"Текст ответа: {result.get('ResponseText')}")
    print(f"Трек-номер: {result.get('Barcode')}")
    print(f"Время ответа: {result.get('ResponseGenTime')}")
