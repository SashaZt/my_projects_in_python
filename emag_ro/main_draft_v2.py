import base64
import json
import sys
import time
from pathlib import Path

import requests
from loguru import logger
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

current_directory = Path.cwd()
data_directory = current_directory / "data"
log_directory = current_directory / "log"


data_directory.mkdir(parents=True, exist_ok=True)
log_directory.mkdir(parents=True, exist_ok=True)

log_file_path = log_directory / "log_message.log"
category_file_path = data_directory / "category.json"

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
        "Accept": "application/json",
        "Authorization": f"Basic {base64_auth}",
        "Content-Type": "application/json",
    }
    api_url_draft = "https://marketplace-api.emag.ro"
    # Настройка сессии с повторными попытками
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return api_url_draft, headers, session


api_url_draft, headers, session = get_headers_session()


# Функция для создания черновика
def get_draft():

    try:
        response = session.get(
            f"{api_url_draft}/api/v1/draft", headers=headers, timeout=30
        )

        if response.status_code == 200:
            with open("draft_get.json", "w") as f:
                json.dump(response.json(), f)
            return response.json()
        else:
            logger.error(
                f"Failed to create draft. Status code: {response.status_code}, Response: {response.text}"
            )
            return {
                "isError": True,
                "status_code": response.status_code,
                "message": response.text,
            }

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        return {"isError": True, "message": str(e)}


# Функция для создания черновика
def create_draft(product_data):

    # Проверка на наличие обязательных полей
    required_fields = ["id", "name", "part_number", "brand"]
    missing_fields = [field for field in required_fields if field not in product_data]

    if missing_fields:
        logger.error(f"Missing mandatory fields: {', '.join(missing_fields)}")
        return {
            "isError": True,
            "message": f"Missing fields: {', '.join(missing_fields)}",
        }

    try:
        response = session.post(
            f"{api_url_draft}/api/v1/draft", headers=headers, json=product_data
        )

        if response.status_code == 200:
            logger.info(
                f"Draft created successfully for product ID: {product_data['id']}"
            )
            return response.json()
        else:
            return {
                "isError": True,
                "status_code": response.status_code,
                "message": response.text,
            }
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        return {"isError": True, "message": str(e)}


# Функция для создания черновика
def updates_draft(product_data):

    # Проверка на наличие обязательных полей
    required_fields = ["id", "name", "part_number", "brand"]
    missing_fields = [field for field in required_fields if field not in product_data]

    if missing_fields:
        logger.error(f"Missing mandatory fields: {', '.join(missing_fields)}")
        return {
            "isError": True,
            "message": f"Missing fields: {', '.join(missing_fields)}",
        }

    try:
        response = session.post(
            f"{api_url_draft}/api/v1/draft", headers=headers, json=product_data
        )

        if response.status_code == 200:
            logger.info(
                f"Draft created successfully for product ID: {product_data['id']}"
            )
            return response.json()
        else:
            logger.error(
                f"Failed to create draft. Status code: {response.status_code}, Response: {response.text}"
            )
            return {
                "isError": True,
                "status_code": response.status_code,
                "message": response.text,
            }

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        return {"isError": True, "message": str(e)}


def get_category():
    api_url = "https://marketplace-api.emag.ro/api-3"
    # Параметры пагинации
    current_page = 1
    items_per_page = 100  # Максимальное количество элементов на странице
    all_results = []

    while True:
        data = {"data": {"currentPage": current_page, "itemsPerPage": items_per_page}}

        response = session.post(
            f"{api_url}/category/read", headers=headers, json=data, timeout=30
        )

        if response.status_code != 200:
            logger.error(f"Ошибка {response.status_code}: {response.text}")
            break

        response_data = response.json()

        if response_data.get("isError"):
            logger.error(f"Ошибка API: {response_data.get('messages')}")
            break

        results = response_data.get("results", [])
        if not results:
            break  # Прекращаем, если больше нет данных

        all_results.extend(results)
        logger.info(f"Загружено {len(all_results)} категорий...")

        current_page += 1

    # Сохранение всех данных в файл
    with open(category_file_path, "w", encoding="utf-8") as json_file:
        json.dump(all_results, json_file, ensure_ascii=False, indent=4)

    logger.info(f"Всего загружено {len(all_results)} категорий")


if __name__ == "__main__":
    # get_category()

    # Пример данных для черновика
    # product_example = {
    #     "id": "1234565",  # Обязательное
    #     "name": "Test product",  # Обязательное
    #     "brand": "Brand name",  # Обязательное
    #     "part_number": "md788hc/aA",  # Обязательное
    #     "category_id": "58",  # Опционально
    #     "ean": "5906476016758",  # Опционально
    #     "source_language": "pl_PL",  # Опционально
    # }
    product_data = {
        # Основные поля товара
        "id": "95117032",  # Обязательное. Integer 1-16777215. Ваш внутренний ID товара
        "category_id": "58",  # Обязательное. Integer 1-65535. ID категории eMAG
        "vendor_category_id": "506",  # Опциональное. Integer. Ваш внутренний ID категории
        # Для привязки к существующему товару
        "part_number_key": "ES0NKBBBD",  # Опциональное. String. Используется для привязки оффера к существующему товару
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
                "id": 24,  # Обязательное. Integer 1-65535. ID характеристики
                "value": "test",  # Обязательное. String 1-255 символов
                "tag": "original",  # Обязательное для характеристик с тегами
            }
        ],
        # Информация о семействе товаров
        "family": {
            "id": 0,  # Обязательное. Integer. 0 для удаления из семейства
            "name": "Test family",  # Обязательное если id не 0
            "family_type_id": 95,  # Обязательное если id не 0. Integer
        },
        # URL и гарантия
        # "url": "http://valid-url.html",  # Опциональное. String 1-1024 символов
        "warranty": "24",  # Обязательное/Опциональное в зависимости от категории. Integer 0-255
        # Штрихкоды
        "ean": "5901122700814",
        # Обязательное/Опциональное в зависимости от категории. Array of strings 6-14 цифр
        # Вложения
        # "attachments": [
        #     {
        #         "id": 123,  # Опциональное. Integer 1-4294967295
        #         "url": "http://valid-url",  # Обязательное. String 1-1024 символов. URL документа
        #     }
        # ],
        # Статус оффера
        "status": 1,  # Обязательное. Integer (0-неактивный, 1-активный, 2-end of life)
        # Цены и валюта
        "sale_price": "2500",  # Обязательное. Decimal >0, до 4 знаков после запятой
        "recommended_price": "2500",  # Опциональное. Decimal >0, больше sale_price
        "min_sale_price": "2400",  # Обязательное при первом сохранении. Decimal >0
        "max_sale_price": "2500",  # Обязательное при первом сохранении. Decimal >0, больше min_sale_price
        "currency_type": "EUR",  # Опциональное. String (EUR/PLN)
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
        # Время поставки и начало продаж
        # "supply_lead_time": 5,  # Опциональное. Integer (2,3,5,7,14,30,60,90,120)
        # "start_date": "2024-12-31",  # Опциональное. YYYY-MM-DD. До 60 дней вперед
        # НДС
        "vat_id": "1",  # Обязательное. Integer
        # eMAG Club
        # "emag_club": 1,  # Опциональное. Integer (0/1). По умолчанию 1
        # GPSR информация
        # "safety_information": "Keep out of reach of children",  # Опциональное. String до 16777215 символов
        # Информация о производителе
        # "manufacturer": [
        #     {
        #         "name": "Company name Ltd.",  # Обязательное в блоке. String 1-200 символов
        #         "address": "Company address",  # Обязательное в блоке. String 1-500 символов
        #         "email": "company@company.com",  # Обязательное в блоке. String 1-100 символов
        #     }
        # ],
        # # Информация о представителе в ЕС
        # "eu_representative": [
        #     {
        #         "name": "EU Company name",  # Обязательное в блоке. String 1-200 символов
        #         "address": "EU address",  # Обязательное в блоке. String 1-500 символов
        #         "email": "eu@company.com",  # Обязательное в блоке. String 1-100 символов
        #     }
        # ],
    }

    # get_draft()
    # # Создание черновика
    response = create_draft(product_data)
    logger.info(response)
