import requests
import json
import time
from datetime import datetime
from config.logger import logger

def get_cookie_value(session, cookie_name, default=""):
    """Безопасно получить значение cookie"""
    for cookie in session.cookies:
        if cookie.name == cookie_name:
            return cookie.value
    return default

def get_all_cookies_dict(session):
    """Безопасно получить все cookies как словарь"""
    cookies_dict = {}
    for cookie in session.cookies:
        cookies_dict[cookie.name] = cookie.value
    return cookies_dict

def login_and_get_data():
    # Создаем сессию для сохранения cookies
    session = requests.Session()
    
    # Первый запрос - авторизация
    logger.info("Выполняем авторизацию...")
    
    login_headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'ru,en;q=0.9,uk;q=0.8',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        'DNT': '1',
        'Origin': 'https://hms6.servio.support',
        'Referer': 'https://hms6.servio.support/HMS_Holosiivskyi/Login.aspx?RequestedURL=https%3A%2F%2Fhms6.servio.support%2FHMS_Holosiivskyi%2FBase%2FLivingGuests.aspx%3Fhotelid%3D1%26valuteid%3D1%26cpw%3Dtrue',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
    }
    
    login_data = {
        '__LASTFOCUS': '',
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        '__VIEWSTATE': 'F2mLoceNsBpVdstm+nA5F8F+7R7zjz3SA3Ep0wy7mUccuWaYV6Mno0Qrb6wHM5hfa7mKsEgXBgyl8QK117Qo4xz2ogSSnwvtu31lT1vMK1fkOyfYQl/T3EkoYCKuzkatQY9QdDFDkk2a3AeIiuGwTU64aC5nWEpSshHeDn+kXxvdbj1DPRpOAM1/LL48Twlpae0aTd0+I0Bjno+hHksJmnBHvMgQU1dVZeMMZnYJEmLdADDPlNZ2rSm+qhT25CYgUx/Eh4bDZD8/kgs1XMA8EPVEt2Sg5bQAzzcdxxxF6sixkBI1aGocqMyND2hf0WTcDUU0qwNj1/u7SJXShQdEsf+ChbS5jg0yuADzDa7ir86b2YqmC2tnet2OEEjtVd0xcC+lfm5QzcGWl5bLoQmGI3REQZyQC1vWAJQwWSoyvV5SdbQwcrhkk4BqxXvAejBdsuKnOkwfuMM7He+8K8VFyO8K3/dzDSpWGNx9MvixXPq9XLLlTYi6+VvPP4qDco87vIkUtjJUYV9RK97tksaq7ZPukTxkc8sneQFkXESSUkMDc8RgD2/rWuCe1F1kJSeQKN+w1pZpPTkP84ZXttKiivC7Gvo0gRvoLMHFlQ/3VXpQ6EZ9GDn/y6lK+UbBa5nsJSxFR0aV79Ok5rcrDi9Npx1VGx1dKyn1E1c725R6pPZBlJ/rvTmEk6Hq6FwGpNtgQow1DomNrrqucO5oCoQNCg==',
        '__VIEWSTATEGENERATOR': '83C04EE5',
        '__EVENTVALIDATION': 'TvWM/TvOujigmn3wGez+EeXVLf5bLGRWxPDzKaL/4TQ0iBu/hBlfPWZajvXQ+3C/zba76ISZ6qAIhHmkHSzlDcLc8rX1djUVuvG/xkjvREFWWG6JxkAtJib2LpczlhcrXuimEs2PvV1IwsImtzKumh2rUr0a/T4nDxMq3M/IlmgfcpNTGOdmQc7wJpUftjuXDrvsiUbRP5853nQQuBz9rqk6jQEwrsdAlvpGFxRH98kONpKb3OdBVT6hp5JjQ7ShVg2M4bmcP6pYGKp9vAZXbuM6J5jCZtUT1eHxWi4WKmWr7Yq7EVpEF4zdGU/o2iRJXi1jmIFBOXT/sp3wkQ+FAGZR0JBwc0q0Tb9QkkkFYm4JVBE1WnMK7rrWZoDwPOioAmIUymMhDjXsVdDE0o9Q4c4ZvCtk/bMpkWE8fLrQWxE2z0hq/thNwDaoGKewYKB+NO3NObVVC9Q9QPVTGj4FyA==',
        'O2C53B92_e8a8ce70': '1',
        'O91395030_3f1e4086': 'uk-UA',
        'OF33B9C8_7733702e': 'Пац Денис',
        'O2AF9712E_1c4b4ac4': 'пац888',
        'O84B27FAB_b65aed21': 'Войти',
    }
    
    # Устанавливаем начальные cookies
    session.cookies.set('ASP.NET_SessionId', 'wdk2aa3lucjtwk1frkgyt1rf')
    logger.info(f"Установлены начальные cookies: ASP.NET_SessionId")
    
    try:
        # Выполняем авторизацию
        logger.info("Отправляем запрос авторизации...")
        login_response = session.post(
            'https://hms6.servio.support/HMS_Holosiivskyi/Login.aspx?RequestedURL=https%3a%2f%2fhms6.servio.support%2fHMS_Holosiivskyi%2fBase%2fLivingGuests.aspx%3fhotelid%3d1%26valuteid%3d1%26cpw%3dtrue',
            headers=login_headers,
            data=login_data,
            timeout=30
        )
        
        logger.info(f"Статус авторизации: {login_response.status_code}")
        
        # Безопасное логирование cookies
        cookies_dict = get_all_cookies_dict(session)
        logger.info(f"Полученные cookies: {cookies_dict}")
        
        # Проверяем ключевые cookies
        session_id = get_cookie_value(session, 'ASP.NET_SessionId')
        hms_culture = get_cookie_value(session, 'HMSCulture')
        last_user = get_cookie_value(session, 'LastUser')
        work_place = get_cookie_value(session, 'WorkPlace')
        
        logger.info(f"Ключевые cookies:")
        logger.info(f"  - ASP.NET_SessionId: {session_id}")
        logger.info(f"  - HMSCulture: {hms_culture}")
        logger.info(f"  - LastUser: {last_user}")
        logger.info(f"  - WorkPlace: {work_place}")
        
    except requests.exceptions.Timeout:
        logger.error("Ошибка: Превышено время ожидания при авторизации")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при авторизации: {e}")
        return None
    
    # Заголовки для API запроса
    api_headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'ru,en;q=0.9,uk;q=0.8',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'DNT': '1',
        'Origin': 'https://hms6.servio.support',
        'Referer': 'https://hms6.servio.support/HMS_Holosiivskyi/Base/LivingGuests.aspx?hotelid=1&valuteid=1&cpw=true',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
    }
    
    # Данные для API запроса
    api_data = {
        "hotelID": 1,
        "valuteID": 1,
        "loginID": 403,
        "onlyLiving": True
    }
    
    logger.info(f"Подготовлены данные для API запроса: {api_data}")
    
    def make_api_request(request_num):
        logger.info(f"Выполняем API запрос #{request_num}...")
        logger.info(f"Время: {datetime.now().strftime('%H:%M:%S')}")
        
        # Показываем текущие cookies перед запросом
        current_cookies = get_all_cookies_dict(session)
        logger.info(f"Используемые cookies для запроса #{request_num}: {current_cookies}")
        
        try:
            api_response = session.post(
                'https://hms6.servio.support/HMS_Holosiivskyi/DataServices/LivingGuests/LivingGuestsService.svc/OCA113821_578b23ab',
                headers=api_headers,
                json=api_data,
                timeout=30
            )
            
            logger.info(f"Статус API запроса #{request_num}: {api_response.status_code}")
            
            if api_response.status_code == 200:
                # Сохраняем ответ в JSON файл
                filename = f'living_guests_response_{request_num}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                
                try:
                    response_json = api_response.json()
                    
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(response_json, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"Ответ сохранен в файл: {filename}")
                    logger.info(f"Размер данных: {len(str(response_json))} символов")
                    
                    # Логируем краткую информацию о содержимом
                    if isinstance(response_json, dict):
                        logger.info(f"Ключи в ответе: {list(response_json.keys())}")
                    elif isinstance(response_json, list):
                        logger.info(f"Получен список из {len(response_json)} элементов")
                    
                    return response_json
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Ошибка: Ответ не является валидным JSON - {e}")
                    logger.error(f"Содержимое ответа: {api_response.text[:500]}...")
                    
                    # Сохраняем как текст
                    error_filename = f'response_text_{request_num}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
                    with open(error_filename, 'w', encoding='utf-8') as f:
                        f.write(api_response.text)
                    
                    logger.info(f"Ответ сохранен как текст в файл: {error_filename}")
                    return None
                    
            else:
                logger.error(f"Ошибка API запроса #{request_num}: {api_response.status_code}")
                logger.error(f"Ответ: {api_response.text[:200]}...")
                
                # Сохраняем ошибку для анализа
                error_filename = f'error_response_{request_num}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
                with open(error_filename, 'w', encoding='utf-8') as f:
                    f.write(f"Status: {api_response.status_code}\n")
                    f.write(f"Headers: {dict(api_response.headers)}\n")
                    f.write(f"Content: {api_response.text}")
                
                logger.info(f"Ошибка сохранена в файл: {error_filename}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"Ошибка: Превышено время ожидания для запроса #{request_num}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса #{request_num}: {e}")
            return None
    
    # Первый API запрос
    logger.info("=== ПЕРВЫЙ API ЗАПРОС ===")
    response1 = make_api_request(1)
    
    if response1 is not None:
        logger.info("Первый запрос выполнен успешно")
    else:
        logger.error("Первый запрос завершился с ошибкой")
    
    # Пауза 15 секунд
    logger.info("Ожидание 15 секунд...")
    for i in range(15, 0, -1):
        if i % 5 == 0 or i <= 3:  # Логируем каждые 5 секунд и последние 3
            logger.info(f"Осталось: {i} сек")
        time.sleep(1)
    
    logger.info("Пауза завершена!")
    
    # Второй API запрос с той же сессией
    logger.info("=== ВТОРОЙ API ЗАПРОС ===")
    response2 = make_api_request(2)
    
    if response2 is not None:
        logger.info("Второй запрос выполнен успешно")
    else:
        logger.error("Второй запрос завершился с ошибкой")
    
    logger.info("Все запросы выполнены!")
    
    # Финальная статистика
    final_cookies = get_all_cookies_dict(session)
    
    return {
        'login_status': login_response.status_code,
        'cookies': final_cookies,
        'response1': response1,
        'response2': response2,
        'session_id': get_cookie_value(session, 'ASP.NET_SessionId'),
        'hms_culture': get_cookie_value(session, 'HMSCulture'),
        'last_user': get_cookie_value(session, 'LastUser'),
        'work_place': get_cookie_value(session, 'WorkPlace')
    }

if __name__ == "__main__":
    try:
        logger.info("=== ЗАПУСК ПРОГРАММЫ ===")
        logger.info(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        result = login_and_get_data()
        
        if result is not None:
            logger.info("=== РЕЗУЛЬТАТ ВЫПОЛНЕНИЯ ===")
            logger.info(f"Статус авторизации: {result['login_status']}")
            logger.info(f"Итоговые cookies: {result['cookies']}")
            logger.info(f"Первый запрос: {'Успешно' if result['response1'] else 'Ошибка'}")
            logger.info(f"Второй запрос: {'Успешно' if result['response2'] else 'Ошибка'}")
            logger.info(f"Session ID: {result['session_id']}")
            logger.info(f"HMS Culture: {result['hms_culture']}")
            logger.info(f"Last User: {result['last_user']}")
            logger.info(f"Work Place: {result['work_place']}")
            
            logger.info("=== ПРОГРАММА ЗАВЕРШЕНА УСПЕШНО ===")
        else:
            logger.error("Программа завершилась с ошибкой - результат None")
            
    except Exception as e:
        logger.error(f"Общая ошибка: {e}")
        logger.error(f"Тип ошибки: {type(e).__name__}")
        import traceback
        logger.error(f"Трейсбек: {traceback.format_exc()}")