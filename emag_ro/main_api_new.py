import base64
import json
import re
import sys
import time
from pathlib import Path

import requests
from loguru import logger
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

current_directory = Path.cwd()
log_directory = current_directory / "log"
log_file_path = log_directory / "log_message.log"

logger.remove()
# 🔹 Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# 🔹 Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)


def get_headers_session():
    # Данные для авторизации
    username = "resteqsp@gmail.com"
    password = "Q7Hd.ATGCc5$ym2"
    auth_string = f"{username}:{password}"
    base64_auth = base64.b64encode(auth_string.encode()).decode()

    # Заголовки запроса
    headers = {
        "Authorization": f"Basic {base64_auth}",
        "Content-Type": "application/json",
    }
    api_url = "https://marketplace-api.emag.ro/api-3"

    # Настройка сессии с повторными попытками
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return api_url, headers, session


# Получаем сессию и заголовки
api_url, headers, session = get_headers_session()


def validate_product_data(product):
    """Проверка обязательных полей продукта"""
    required_fields = [
        "id",
        "category_id",
        "name",
        "part_number",
        "brand",
        "description",
        "status",
        "sale_price",
        "vat_id",
        "stock",
        "handling_time",
    ]

    missing_fields = [field for field in required_fields if field not in product]
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

    # Проверка характеристик
    if "characteristics" in product:
        for char in product["characteristics"]:
            if not all(key in char for key in ["id", "value"]):
                raise ValueError("Invalid characteristic format")

    # Проверка stock
    if not isinstance(product["stock"], list) or not product["stock"]:
        raise ValueError("Stock must be a non-empty list")

    # Проверка handling_time
    if not isinstance(product["handling_time"], list) or not product["handling_time"]:
        raise ValueError("Handling time must be a non-empty list")


def get_vat_rates():
    response = session.post(f"{api_url}/vat/read", headers=headers)
    vat_rates = response.json()
    # Сохраняем vat_rates в файл vat_rates.json
    vat_rates_file_path = current_directory / "vat_rates.json"
    with open(vat_rates_file_path, "w", encoding="utf-8") as vat_file:
        json.dump(vat_rates, vat_file, ensure_ascii=False, indent=4)


def clean_description(description):
    # Паттерн для поиска img тегов с base64
    pattern = (
        r'<img[^>]*?class="lazy"[^>]*?data-src="([^"]*)"[^>]*?src="data:image[^>]*?>'
    )

    # Замена на чистый img тег
    cleaned = re.sub(pattern, r'<img src="\1" alt="Product Image"/>', description)

    # Убираем пустые атрибуты
    cleaned = re.sub(r'\s+(?:height|width|style|align)=["\']\s*["\']', "", cleaned)

    return cleaned


def upload_product(product_data):
    try:

        # Проверяем наличие ключа data и что это список
        if not isinstance(product_data.get("data"), list):
            raise ValueError("Data should be a list of products")

        # Проверяем каждый продукт в списке
        for product in product_data["data"]:
            validate_product_data(product)

        # Конвертируем строковые значения в числовые
        for product in product_data["data"]:
            product["id"] = int(product["id"])
            product["category_id"] = int(product["category_id"])
            product["status"] = int(product["status"])
            product["sale_price"] = float(product["sale_price"])
            product["min_sale_price"] = float(product["min_sale_price"])
            product["max_sale_price"] = float(product["max_sale_price"])
            product["vat_id"] = int(product["vat_id"])
            product["warranty"] = int(product["warranty"])

        # Отправляем запрос
        response = session.post(
            f"{api_url}/product_offer/save", headers=headers, json=product_data
        )

        # Проверяем ответ
        response.raise_for_status()
        result = response.json()

        # Проверяем на ошибки в ответе eMAG
        if result.get("isError"):
            error_messages = result.get("messages", [])
            raise Exception(f"eMAG API Error: {error_messages}")

        # Проверяем наличие документационных ошибок
        if "doc_errors" in result:
            logger.warning(f"Documentation errors: {result['doc_errors']}")

        return result

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise


# Пример использования
try:
    # Ваши данные продукта
    product_data = {
        "data": [  # Оборачиваем в массив data
            {
                # Основные поля товара
                "id": "95117032",  # Обязательное. Integer 1-16777215. Ваш внутренний ID товара
                "category_id": "58",  # Обязательное. Integer 1-65535. ID категории eMAG
                "vendor_category_id": "506",  # Опциональное. Integer. Ваш внутренний ID категории
                # Для привязки к существующему товару
                # "part_number_key": "ES0NKBBBD",  # Опциональное. String. Используется для привязки оффера к существующему товару
                # Языковые настройки
                "source_language": "ro_RO",  # Опциональное. String. Язык контента (ro_RO, bg_BG, hu_HU и др.)
                # Основная информация о товаре
                "name": "Aspirator vertical, Roidmi, X20S, Alb/Negru, Fara fir, 2 in 1, Functie mop, Putere 435W, Rezervor 0,4 l, Baterie 2500 mAh, Filtrare in 6 etape, Accesorii incluse",  # Обязательное. String 1-255 символов. Название товара
                "part_number": "md788hc/d",  # Обязательное. String 1-25 символов. Уникальный идентификатор производителя
                "description": '<h2><strong>Aspirator vertical, Roidmi, X20S, Alb/Negru, Fara fir, 2in 1, Functie mop, Putere 435W, Rezervor 0,4 l, Baterie 2500 mAh, Filtrare in 6 etape, Acesorii incluse</strong></h2><p><strong>Aspirator vertical Roidmi fara fir</strong><br/> Experimentati ca curatarea poate fi convenabila! Aspiratorul vertical fara fir de la Roidmi va aspira si va curata podelele din casa dumneavoastra. Detineti un apartament sau o casa mai mare? Perfect! Bateriile de 2500 mAh (fiecare) asigura o durata de functionare impresionanta. X20S functioneaza la 1.200.000 de rotatii pe minut, iar puterea de aspirare ajunge la 138 de wati, astfel incat sa fii sigur ca apartamentul tau va fi sclipitor de curat. Accesoriile incluse sunt grozave pentru curatarea tuturor tipurilor de suprafete, iar incarcarea fara fir va va permite sa scapati de fire. Vezi cu ce te mai poate surprinde!</p><p><strong> </strong><img align="" alt="Unknown Image" class="lazy" data-src="https://b2b.innpro.pl/data/include/cms/03Roidmi/X20S/10.jpg" height="" src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" style="" width=""/><br/><strong>Dispozitiv 2 in 1</strong><br/> Cu X20S va puteti aspira si curata podelele. Pur si simplu inlocuiti peria cu mopul (inclus). Capul periei de mop electric se roteste la aproximativ 200 rpm, curatand bine suprafetele. Pete uleioase pe gresie de bucatarie, reziduuri alimentare - Aspiratorul Roidmi este gata pentru asta!</p><img align="" alt="Unknown Image" class="lazy" data-src="https://b2b.innpro.pl/data/include/cms/03Roidmi/X20S/10.jpg" height="" src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" style="" width=""/><p><strong> </strong><img align="" alt="Unknown Image" class="lazy" data-src="https://rcpro.pl/data/include/cms/03Roidmi/X20S/18.jpg" height="" src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" style="" width=""/><br/><strong>Solutii inovative</strong><br/> Peria electrica pentru mopul foloseste un cip inteligent pentru a controla nivelul apei. Drept urmare, dupa spalare, suprafata se usuca rapid si va puteti deplasa liber prin apartament. Rezervorul contine 240 ml de apa si puteti alege, de asemenea, intre 2 moduri pentru cantitatea de apa distribuita. Si asta nu este tot! Pentru a va usura lucrurile, X20S dispune de o statie de auto-curatare care curata peria de mop si apoi o usuca. Bucurati-va de solutiile inovatoare pe care le ofera Roidmi!</p><img align="" alt="Unknown Image" class="lazy" data-src="https://rcpro.pl/data/include/cms/03Roidmi/X20S/18.jpg" height="" src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" style="" width=""/><p><strong> </strong><img align="" alt="Unknown Image" class="lazy" data-src="https://rcpro.pl/data/include/cms/03Roidmi/X20S/15.jpg" height="" src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" style="" width=""/><br/><strong>Perie electrica eficienta</strong><br/> Peria electrica pentru podea are o rola de tip nou HL. Lungimea perilor ajunge la 1 mm, astfel incat nu numai ca culeaga murdaria si parul mai mare, ci si indeparteaza eficient praful ascuns in crapaturi. Este perfect pentru diverse tipuri de suprafete, de exemplu, gresie, covoare etc.</p><img align="" alt="Unknown Image" class="lazy" data-src="https://rcpro.pl/data/include/cms/03Roidmi/X20S/15.jpg" height="" src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" style="" width=""/><p><strong> </strong><img align="" alt="Unknown Image" class="lazy" data-src="https://rcpro.pl/data/include/cms/03Roidmi/X20S/9.jpg" height="" src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" style="" width=""/><br/><strong>Motor fara perii de noua generatie si tehnologie Air-x</strong><br/> Noua generatie de motoare digitale cu motor-x fara perii cu viteze de pana la 120.000 rpm si designul inovator al conductei de aer fac ca X20S sa aiba o putere de aspiratie de 138 wati si o presiune a aerului de admisie de 25.000 Pa. In plus, utilizarea tehnologiei Air-x separa eficient aerul de praf fara a bloca filtrul sau a reduce puterea de aspirare.</p><img align="" alt="Unknown Image" class="lazy" data-src="https://rcpro.pl/data/include/cms/03Roidmi/X20S/9.jpg" height="" src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" style="" width=""/><p><strong> </strong><img align="" alt="Unknown Image" class="lazy" data-src="https://rcpro.pl/data/include/cms/03Roidmi/X20S/13.jpg" height="" src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" style="" width=""/><br/><strong>Timp de lucru 65 min</strong><br/> Sistemul BMS-X extinde durata de functionare prin optimizarea inteligenta a gestionarii a 8 baterii cu litiu LG/Samsung. Mai mult, aplicatia va va informa despre starea bateriei si va afisa orice problema intalnita. Dispozitivul este echipat cu o putere totala de 435 de wati, in timp ce durata de functionare a lui X20S ajunge la aproximativ 65 de minute.</p><img align="" alt="Unknown Image" class="lazy" data-src="https://rcpro.pl/data/include/cms/03Roidmi/X20S/13.jpg" height="" src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" style="" width=""/><p><strong> </strong><img align="" alt="Unknown Image" class="lazy" data-src="https://rcpro.pl/data/include/cms/03Roidmi/X20S/2.jpg" height="" src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" style="" width=""/><br/><strong>Filtrare in 6 etape</strong><br/> Ofera un mediu curat si sigur pentru familia ta! Unitatea are un sistem de filtrare in mai multe etape care separa eficient praful de aer. Chiar si cele mai mici impuritati de 0,3 μm sunt filtrate, iar rata de purificare ajunge la 99%. In plus, unitatea va inceta sa functioneze daca uitati sa instalati una dintre numeroasele parti ale sistemului de filtrare. Acest lucru asigura protectia X20S si siguranta utilizatorului.</p><img align="" alt="Unknown Image" class="lazy" data-src="https://rcpro.pl/data/include/cms/03Roidmi/X20S/2.jpg" height="" src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" style="" width=""/><p><img align="" alt="Unknown Image" class="lazy" data-src="https://rcpro.pl/data/include/cms/03Roidmi/X20S/12.jpg" height="" src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" style="" width=""/><strong> <br/> Diverse scenarii de curatare</strong><br/> Setul vine cu accesorii pe care le vei folosi in functie de suprafata pe care o cureti. Peria pentru acarieni elimina eficient alergenii care persista in saltele, iar peria multifunctionala va fi la indemana atunci cand curatati suprafetele neuniforme, de exemplu, tastatura computerului. Pentru a scapa de murdaria de pe suprafetele inguste si greu accesibile, utilizati peria pentru crapaturi.</p><img align="" alt="Unknown Image" class="lazy" data-src="https://rcpro.pl/data/include/cms/03Roidmi/X20S/12.jpg" height="" src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" style="" width=""/><p><strong> </strong><img align="" alt="Unknown Image" class="lazy" data-src="https://rcpro.pl/data/include/cms/03Roidmi/X20S/5.jpg" height="" src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" style="" width=""/><br/><strong>Gardianul tau pentru curatenia casei</strong><br/> Instalati aplicatia pentru a obtine acces la functii utile! Dispozitivul se conecteaza prin Bluetooth la smartphone-ul dvs., iar aplicatia va permite sa verificati timpul ramas de functionare sau de curatare. De asemenea, va va trimite o notificare cand recipientul de praf este plin si filtrul trebuie inlocuit.</p><img align="" alt="Unknown Image" class="lazy" data-src="https://rcpro.pl/data/include/cms/03Roidmi/X20S/5.jpg" height="" src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" style="" width=""/><p><strong> </strong><img align="" alt="Unknown Image" class="lazy" data-src="https://rcpro.pl/data/include/cms/03Roidmi/X20S/7.jpg" height="" src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" style="" width=""/><br/><strong>Incarcare magnetica fara fir</strong><br/> Eliberati-va de fire si obtineti o modalitate convenabila de a va incarca X20S. Aspiratorul Roidmi accepta incarcarea fara fir, pentru si mai mult confort. Pur si simplu montati statia de incarcare pe perete si atasati dispozitivul la ea. Dureaza doar aproximativ 2,5 ore pentru ca aspiratorul sa fie gata de utilizare din nou.</p><img align="" alt="Unknown Image" class="lazy" data-src="https://rcpro.pl/data/include/cms/03Roidmi/X20S/7.jpg" height="" src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" style="" width=""/><p><img align="" alt="Unknown Image" class="lazy" data-src="https://rcpro.pl/data/include/cms/03Roidmi/X20S/6.jpg" height="" src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" style="" width=""/><strong> <br/> Design usor de utilizat</strong><br/> X20S este proiectat pentru a fi simplu si placut de utilizat. Designul atent gandit ofera un nivel de zgomot cu 10% mai mic, rezultand un nivel de zgomot de aproximativ 72 dB (A). Peria electrica inovatoare este echipata cu o lampa LED, ceea ce face curatarea suprafetei de sub pat sau canapea convenabila si minutioasa. In plus, greutatea de 1,5 kg a dispozitivului va permite sa indepartati cu usurinta praful de pe mobilier si perdele inalte.</p><img align="" alt="Unknown Image" class="lazy" data-src="https://rcpro.pl/data/include/cms/03Roidmi/X20S/6.jpg" height="" src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" style="" width=""/><p><strong> </strong><img align="" alt="Unknown Image" class="lazy" data-src="https://rcpro.pl/data/include/cms/03Roidmi/X20S/8.jpg" height="" src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" style="" width=""/><br/><strong>Design minimalist</strong><br/> Designul lui X20S a fost recunoscut cu numeroase premii. Utilizarea alb-negru neutru ofera dispozitivului un aspect clasic, dar elegant. Deci se imbina perfect cu orice interior.</p><img align="" alt="Unknown Image" class="lazy" data-src="https://rcpro.pl/data/include/cms/03Roidmi/X20S/8.jpg" height="" src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" style="" width=""/><p><strong> </strong><img align="" alt="Unknown Image" class="lazy" data-src="https://rcpro.pl/data/include/cms/03Roidmi/X20S/22.jpg" height="" src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" style="" width=""/></p><img align="" alt="Unknown Image" class="lazy" data-src="https://rcpro.pl/data/include/cms/03Roidmi/X20S/22.jpg" height="" src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" style="" width=""/><p><strong>In cutie</strong></p><ul><li>Aspirator</li> <li>Tub pentru aspirator</li> <li>Statie de curatenie</li> <li>Cap de mop x2</li> <li>Perie de mop</li> <li>Perie electrica pentru podea</li> <li>Perie pentru indepartarea acarienilor de praf</li> <li>Perie pentru crapaturi</li> <li>Perie multifunctionala</li> <li>Filtru</li> <li>Incarcator fara fir</li> </ul><li>Aspirator</li><li>Tub pentru aspirator</li><li>Statie de curatenie</li><li>Cap de mop x2</li><li>Perie de mop</li><li>Perie electrica pentru podea</li><li>Perie pentru indepartarea acarienilor de praf</li><li>Perie pentru crapaturi</li><li>Perie multifunctionala</li><li>Filtru</li><li>Incarcator fara fir</li>',  # Опциональное. String до 16777215 символов. HTML допустим
                "brand": "ROIDMI",  # Обязательное. String 1-255 символов
                # Настройки изображений
                "force_images_download": 0,  # Опциональное. Integer (0/1). Принудительное обновление изображений
                "images": [
                    {
                        "display_type": 1,  # Опциональное. Integer 0-2 (0-прочие, 1-основное, 2-дополнительное)
                        "url": "https://s13emagst.akamaized.net/products/42426/42425604/images/res_d59ae9024bc69d4a12b81e02f248ab80.jpg?width=720&amp;height=720&amp;hash=B469B7084231BFDE9B7C2343535C993A",  # Обязательное. String 1-1024 символов. URL изображения
                    }
                ],
                # # Характеристики товара
                "characteristics": [
                    {
                        "id": 5704,  # Product type (обязательное поле, is_mandatory: 1)
                        "value": "Aspirator vertical cu spalare",
                    },
                    {"id": 8434, "value": "Rezidential"},  # Usage
                    {
                        "id": 6903,  # Power type (обязательное поле, is_mandatory: 1)
                        "value": "Acumulator",
                    },
                    {"id": 6917, "value": "Uscata Cu spalare"},  # Vacuum type
                    {
                        "id": 6922,  # Floor Type
                        "value": "Covoare, Podele, Podele dure, Multi-suprafete, Tapiterie",
                    },
                    {"id": 6878, "value": "1.5 kg"},
                    {"id": 5401, "value": "Alb"},
                    {"id": 6866, "value": "435 W"},  # Power
                    {
                        "id": 6932,  # Collection capacity (обязательное поле, is_mandatory: 1)
                        "value": "0.4 l",
                    },
                    {"id": 6935, "value": "HEPA"},  # Exhaust filter
                ],
                # Информация о семействе товаров
                "family": {
                    "id": 0,  # Обязательное. Integer. 0 для удаления из семейства
                    "name": "Test family",  # Обязательное если id не 0
                    "family_type_id": 95,  # Обязательное если id не 0. Integer
                },
                "warranty": "24",  # Обязательное/Опциональное в зависимости от категории. Integer 0-255
                # Штрихкоды
                # Штрихкоды
                "ean": [
                    "5901122700814"
                ],  # EAN должен быть массивом, даже если один код
                # Статус оффера
                "status": 1,  # Обязательное. Integer (0-неактивный, 1-активный, 2-end of life)
                # Цены и валюта
                "sale_price": "2500",  # Обязательное. Decimal >0, до 4 знаков после запятой
                "recommended_price": "2500",  # Опциональное. Decimal >0, больше sale_price
                "min_sale_price": "2400",  # Обязательное при первом сохранении. Decimal >0
                "max_sale_price": "2500",  # Обязательное при первом сохранении. "currency_type": "RON",  # Для Румынии
                "currency_type": "RON",  # Для Румынии
                # Склад и обработка
                "stock": [
                    {
                        "warehouse_id": 1,  # Обязательное в массиве stock. Integer
                        "value": 20,  # Обязательное в массиве stock. Integer 0-65535
                    }
                ],
                # # Время обработки
                "handling_time": [
                    {
                        "warehouse_id": 1,  # Обязательное в массиве handling_time. Integer
                        "value": 0,  # Обязательное в массиве handling_time. Integer 0-255
                    }
                ],
                # НДС
                "vat_id": "4003",  # Обязательное. Integer
            }
        ]
    }
    product_data["data"][0]["description"] = clean_description(
        product_data["data"][0]["description"]
    )

    result = upload_product(product_data)
    logger.info("Product uploaded successfully!")
    logger.info("Response:", json.dumps(result, indent=2))

except Exception as e:
    logger.error(f"Error uploading product: {str(e)}")
