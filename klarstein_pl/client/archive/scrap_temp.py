import asyncio
import aiohttp
import ssl
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

# Ваши данные ScraperAPI
SCRAPERAPI_PROXY = "http://scraperapi:b7141d2b54426945a9f0bf6ab4c7bc54@proxy-server.scraperapi.com:8001"
TEST_URL = "https://httpbin.org/ip"  # Простой тест для проверки IP
TARGET_URL = "https://www.klarstein.pl/Male-AGD/Raclette/Szechuan-hot-pot-patelnia-z-plyta-grillowa-2-w-1-5-l-1350-600-W-Czerwony.html"

async def test_aiohttp_with_proxy():
    """Тест 1: Обычный aiohttp с прокси"""
    logger.info("🧪 Тест 1: aiohttp с ScraperAPI прокси")
    
    # Отключаем SSL верификацию
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    
    try:
        async with aiohttp.ClientSession(connector=connector) as session:
            proxy_url = SCRAPERAPI_PROXY
            
            # Тест 1.1: Проверка IP
            logger.info(f"📡 Тестируем IP через прокси: {proxy_url}")
            async with session.get(TEST_URL, proxy=proxy_url, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ IP через прокси: {data.get('origin', 'Unknown')}")
                else:
                    logger.error(f"❌ HTTP {response.status}")
            
            # Тест 1.2: Целевой сайт
            logger.info(f"🎯 Тестируем целевой сайт")
            async with session.get(TARGET_URL, proxy=proxy_url, timeout=30) as response:
                if response.status == 200:
                    content = await response.text()
                    logger.info(f"✅ Целевой сайт: получено {len(content)} символов")
                    return True
                else:
                    logger.error(f"❌ Целевой сайт: HTTP {response.status}")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ aiohttp ошибка: {e}")
        return False


async def test_rnet_with_proxy():
    """Тест 2: rnet с прокси"""
    logger.info("🧪 Тест 2: rnet с ScraperAPI прокси")
    
    try:
        from rnet import Impersonate, Client, Proxy
        
        # Создаем клиент с прокси
        proxies = [Proxy.all(SCRAPERAPI_PROXY)]
        
        client = Client(
            impersonate=Impersonate.Chrome134,
            proxies=proxies,
            timeout=30
        )
        
        try:
            # Тест IP
            logger.info(f"📡 rnet: Тестируем IP")
            response = await client.get(TEST_URL)
            if response.status_code == 200:
                data = await response.json()
                logger.info(f"✅ rnet IP: {data.get('origin', 'Unknown')}")
            
            # Тест целевого сайта
            logger.info(f"🎯 rnet: Тестируем целевой сайт")
            response = await client.get(TARGET_URL)
            if response.status_code == 200:
                content = await response.text()
                logger.info(f"✅ rnet целевой сайт: получено {len(content)} символов")
                return True
            else:
                logger.error(f"❌ rnet HTTP {response.status_code}")
                return False
                
        finally:
            # Закрываем клиент
            if hasattr(client, 'close'):
                await client.close()
                
    except ImportError:
        logger.warning("⚠️ rnet не установлен, пропускаем тест")
        return False
    except Exception as e:
        logger.error(f"❌ rnet ошибка: {e}")
        return False


async def test_curl_cffi_with_proxy():
    """Тест 3: curl_cffi с прокси"""
    logger.info("🧪 Тест 3: curl_cffi с ScraperAPI прокси")
    
    try:
        from curl_cffi.requests import AsyncSession
        
        async with AsyncSession() as session:
            proxy_config = {
                "http": SCRAPERAPI_PROXY,
                "https": SCRAPERAPI_PROXY
            }
            
            # Тест IP
            logger.info(f"📡 curl_cffi: Тестируем IP")
            response = await session.get(
                TEST_URL,
                proxies=proxy_config,
                impersonate="chrome120",
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ curl_cffi IP: {data.get('origin', 'Unknown')}")
            
            # Тест целевого сайта
            logger.info(f"🎯 curl_cffi: Тестируем целевой сайт")
            response = await session.get(
                TARGET_URL,
                proxies=proxy_config,
                impersonate="chrome120",
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                content = response.text
                logger.info(f"✅ curl_cffi целевой сайт: получено {len(content)} символов")
                return True
            else:
                logger.error(f"❌ curl_cffi HTTP {response.status_code}")
                return False
                
    except ImportError:
        logger.warning("⚠️ curl_cffi не установлен, пропускаем тест")
        return False
    except Exception as e:
        logger.error(f"❌ curl_cffi ошибка: {e}")
        return False


async def test_without_proxy():
    """Тест 4: Запрос без прокси для сравнения"""
    logger.info("🧪 Тест 4: Запрос без прокси (для сравнения)")
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    
    try:
        async with aiohttp.ClientSession(connector=connector) as session:
            # Проверка IP без прокси
            async with session.get(TEST_URL, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ IP без прокси: {data.get('origin', 'Unknown')}")
                    return True
                    
    except Exception as e:
        logger.error(f"❌ Запрос без прокси: {e}")
        return False


async def test_scraperapi_direct():
    """Тест 5: Прямой запрос к ScraperAPI API"""
    logger.info("🧪 Тест 5: Прямой ScraperAPI API")
    
    try:
        # Используем ScraperAPI напрямую через их API
        api_key = "b7141d2b54426945a9f0bf6ab4c7bc54"
        api_url = f"http://api.scraperapi.com/?api_key={api_key}&url={TARGET_URL}"
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(api_url, timeout=30) as response:
                if response.status == 200:
                    content = await response.text()
                    logger.info(f"✅ ScraperAPI прямой API: получено {len(content)} символов")
                    return True
                else:
                    logger.error(f"❌ ScraperAPI API: HTTP {response.status}")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ ScraperAPI API ошибка: {e}")
        return False


async def main():
    """Запуск всех тестов"""
    logger.info("🚀 Начинаем тестирование ScraperAPI")
    logger.info("=" * 60)
    
    results = {}
    
    # Тест 1: aiohttp
    results['aiohttp'] = await test_aiohttp_with_proxy()
    logger.info("=" * 60)
    
    # Тест 2: rnet
    results['rnet'] = await test_rnet_with_proxy()
    logger.info("=" * 60)
    
    # Тест 3: curl_cffi
    results['curl_cffi'] = await test_curl_cffi_with_proxy()
    logger.info("=" * 60)
    
    # Тест 4: без прокси
    results['no_proxy'] = await test_without_proxy()
    logger.info("=" * 60)
    
    # Тест 5: ScraperAPI прямой API
    results['scraperapi_direct'] = await test_scraperapi_direct()
    logger.info("=" * 60)
    
    # Результаты
    logger.info("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ:")
    for method, success in results.items():
        status = "✅ Работает" if success else "❌ Не работает"
        logger.info(f"  {method:15} : {status}")
    
    # Рекомендации
    logger.info("\n💡 РЕКОМЕНДАЦИИ:")
    working_methods = [method for method, success in results.items() if success]
    
    if working_methods:
        logger.info(f"✅ Работающие методы: {', '.join(working_methods)}")
        if 'curl_cffi' in working_methods:
            logger.info("🎯 Рекомендуем использовать curl_cffi")
        elif 'aiohttp' in working_methods:
            logger.info("🎯 Рекомендуем использовать aiohttp")
        elif 'scraperapi_direct' in working_methods:
            logger.info("🎯 Рекомендуем использовать прямой API ScraperAPI")
    else:
        logger.info("❌ Ни один метод не работает - проверьте ScraperAPI ключ")


if __name__ == "__main__":
    asyncio.run(main())