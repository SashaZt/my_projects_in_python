#!/usr/bin/env python3
import asyncio
import datetime
import json
import os
import sys

from loguru import logger

try:
    import nodriver as uc
except ImportError:
    print("Установка nodriver...")
    import subprocess

    subprocess.check_call([sys.executable, "-m", "pip", "install", "nodriver"])
    import nodriver as uc

# Простые пути в домашней директории пользователя
home_dir = os.path.expanduser("~")
work_dir = os.path.join(home_dir, "tikleap_work")
cookies_dir = os.path.join(work_dir, "cookies")

# Создаем рабочую директорию
try:
    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(cookies_dir, exist_ok=True)
    print(f"✅ Рабочая директория: {work_dir}")
except Exception as e:
    print(f"❌ Ошибка создания директории: {e}")
    # Используем /tmp как fallback
    work_dir = "/tmp/tikleap_work"
    cookies_dir = os.path.join(work_dir, "cookies")
    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(cookies_dir, exist_ok=True)
    print(f"🔄 Используем временную директорию: {work_dir}")

logger.remove()

# 🔹 Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)


async def get_cookies(browser):
    """
    Исправленная функция извлечения cookies для nodriver
    """
    try:
        # ========= ИЗВЛЕЧЕНИЕ ВСЕХ COOKIES =========
        logger.info("Начинаем извлечение cookies...")

        # Получить все cookies как список объектов Cookie
        all_cookies = await browser.cookies.get_all()
        logger.info(f"Получено {len(all_cookies)} cookies")

        if not all_cookies:
            logger.warning("Cookies не найдены")
            return {}

        # ========= ПОИСК КОНКРЕТНЫХ COOKIES =========
        target_cookies = {}
        important_keys = ["XSRF-TOKEN", "tikleap_session"]

        # Поиск нужных cookies
        for cookie in all_cookies:
            try:
                # Используем атрибуты объекта Cookie, а не .get()
                cookie_name = cookie.name if hasattr(cookie, "name") else ""
                cookie_value = cookie.value if hasattr(cookie, "value") else ""

                if cookie_name in important_keys:
                    target_cookies[cookie_name] = cookie_value
                    logger.success(
                        f"Найден cookie: {cookie_name} = {cookie_value[:20]}..."
                    )

            except Exception as e:
                logger.error(f"Ошибка при обработке cookie: {e}")
                continue

        # Поиск cookies по частичному совпадению имени
        for cookie in all_cookies:
            try:
                cookie_name = (
                    cookie.name.lower()
                    if hasattr(cookie, "name") and cookie.name
                    else ""
                )
                cookie_value = cookie.value if hasattr(cookie, "value") else ""

                # Поиск по ключевым словам
                if any(
                    keyword in cookie_name
                    for keyword in ["xsrf", "csrf", "token", "session"]
                ):
                    if cookie.name not in target_cookies:
                        target_cookies[cookie.name] = cookie_value
                        logger.info(
                            f"Дополнительный cookie: {cookie.name} = {cookie_value[:20]}..."
                        )

            except Exception as e:
                logger.error(f"Ошибка при поиске дополнительных cookies: {e}")
                continue

        # ========= ПРЕОБРАЗОВАНИЕ В СЛОВАРИ ДЛЯ СОХРАНЕНИЯ =========

        # Преобразуем объекты Cookie в словари для JSON
        cookies_for_json = []
        for cookie in all_cookies:
            try:
                cookie_dict = {
                    "name": getattr(cookie, "name", ""),
                    "value": getattr(cookie, "value", ""),
                    "domain": getattr(cookie, "domain", ""),
                    "path": getattr(cookie, "path", "/"),
                    "secure": getattr(cookie, "secure", False),
                    "httpOnly": getattr(cookie, "httpOnly", False),
                    "sameSite": getattr(cookie, "sameSite", "None"),
                    "expires": getattr(cookie, "expires", None),
                }
                cookies_for_json.append(cookie_dict)
            except Exception as e:
                logger.error(f"Ошибка преобразования cookie в словарь: {e}")

        # ========= СОХРАНЕНИЕ COOKIES =========
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        # ИСПРАВЛЕНО: Используем os.path.join вместо / оператора
        important_cookies_file = os.path.join(cookies_dir, "cookies_important.json")
        cookie_data = {
            "timestamp": timestamp,
            "created_at": datetime.datetime.now().isoformat(),
            "expires_at": (
                datetime.datetime.now() + datetime.timedelta(days=5)
            ).isoformat(),
            "cookies": target_cookies,
            "total_cookies": len(all_cookies),
        }

        with open(important_cookies_file, "w", encoding="utf-8") as f:
            json.dump(cookie_data, f, indent=4, ensure_ascii=False)
        logger.info(f"Важные cookies сохранены в {important_cookies_file}")

        logger.info("🍪 Найденные важные cookies:")
        for name, value in target_cookies.items():
            logger.info(f"  {name}: {value[:30]}{'...' if len(value) > 30 else ''}")

        # Статистика
        logger.info(f"📊 Статистика:")
        logger.info(f"   Всего cookies: {len(all_cookies)}")
        logger.info(f"   Важных cookies: {len(target_cookies)}")
        logger.info(
            f"   Действительны до: {datetime.datetime.now() + datetime.timedelta(days=5)}"
        )

        # Вывод всех cookies для отладки
        logger.debug("📋 Все cookies:")
        for cookie in all_cookies:
            try:
                name = getattr(cookie, "name", "Unknown")
                value = getattr(cookie, "value", "")
                domain = getattr(cookie, "domain", "")
                logger.debug(f"  {name} = {value[:20]}... (domain: {domain})")
            except:
                continue

        return target_cookies

    except Exception as e:
        logger.error(f"Ошибка в функции get_cookies: {e}")
        logger.exception("Подробности ошибки:")
        return {}


async def main():
    browser = None  # Инициализируем переменную
    try:
        browser_args = []
        # browser_args = ["--headless=new"]

        # Инициализируем браузер с обработкой ошибок
        logger.info("Инициализация браузера...")
        try:
            browser = await uc.start(
                headless=False,  # GUI режим для Docker VNC
                browser_args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--window-size=1800,1000",
                ],
            )
            if not browser:
                logger.error("Браузер не инициализирован")
                return

            logger.success("Браузер успешно запущен")

        except Exception as e:
            logger.error(f"Ошибка инициализации браузера: {e}")
            return

        # Переход на страницу логина
        logger.info("Переходим на страницу логина...")
        try:
            login_page = await browser.get("https://www.tikleap.com/login")
            if not login_page:
                logger.error("Не удалось получить страницу логина (вернула None)")
                return
            logger.info(f"Текущий URL после навигации: {login_page.url}")
        except Exception as e:
            logger.error(f"Ошибка при навигации на страницу логина: {str(e)}")
            return

        await asyncio.sleep(2)

        # Вводим email
        logger.info("Вводим email...")
        email_field = await login_page.select("input#email")
        if email_field:
            await email_field.send_keys("37200@starlivemail.com")
            await asyncio.sleep(0.5)
            logger.success("Email введен")
        else:
            logger.warning("Поле email не найдено!")

        # Вводим пароль
        logger.info("Вводим пароль...")
        password_field = await login_page.select("input#password")
        if password_field:
            await password_field.send_keys("bfnsa232@1!dsA")
            await asyncio.sleep(0.5)
            logger.success("Пароль введен")
        else:
            logger.warning("Поле пароля не найдено!")

        # Ищем кнопку логина
        logger.info("Ищем кнопку логина...")
        login_button = await login_page.select(".form-action button")

        if not login_button:
            login_button = await login_page.find("Log In", best_match=True)
            logger.info("Использую поиск по тексту для кнопки")

        if not login_button:
            login_button = await login_page.select("form button")
            logger.info("Использую поиск кнопки на форме")

        if login_button:
            logger.info("Кнопка логина найдена. Нажимаем...")
            await asyncio.sleep(1)

            try:
                await login_button.click()
                logger.info("Нажали на кнопку входа через .click()")
            except Exception as e:
                logger.error(f"Ошибка при нажатии кнопки через click(): {e}")
                try:
                    await login_button.mouse_click()
                    logger.info("Нажали на кнопку входа через .mouse_click()")
                except Exception as e:
                    logger.error(f"Ошибка при нажатии кнопки через mouse_click(): {e}")

            logger.info("Ждем обработки входа...")
            await asyncio.sleep(5)
        else:
            logger.warning("Кнопка логина не найдена!")

        # Извлечение cookies
        logger.info("🍪 Начинаем извлечение cookies...")
        extracted_cookies = await get_cookies(browser)

        if extracted_cookies:
            logger.success("🎉 Cookies успешно извлечены!")
            logger.info(f"📁 Cookies сохранены в: {cookies_dir}")
            logger.info("🔄 Cookies можно использовать в headless режиме 5 дней")
        else:
            logger.error("❌ Не удалось извлечь важные cookies")

    except Exception as e:
        logger.error(f"Произошла ошибка: {str(e)}")
        logger.exception("Подробности ошибки:")

    finally:
        # ИСПРАВЛЕНО: Проверяем что browser не None
        if browser is not None and hasattr(browser, "stop"):
            try:
                logger.info("⏳ Закрытие браузера через 5 секунд...")
                await asyncio.sleep(5)
                await browser.stop()
                logger.info("🔒 Браузер закрыт")
            except Exception as e:
                logger.error(f"Ошибка при закрытии браузера: {e}")


if __name__ == "__main__":
    logger.info("🎬 Запуск TikLeap авторизации (Docker + VNC версия)")
    uc.loop().run_until_complete(main())
