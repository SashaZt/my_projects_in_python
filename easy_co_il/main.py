import asyncio
import json
import os
from datetime import datetime

import nodriver as uc


async def main():
    # Создаем папку json, если она не существует
    os.makedirs("json", exist_ok=True)

    # Запускаем браузер
    config = uc.Config(
        headless=False,  # Браузер виден
        browser_args=[
            "--disable-blink-features=AutomationControlled",  # Обход обнаружения автоматизации
            "--ignore-certificate-errors",
        ],
    )
    browser = await uc.start(config=config)

    # Получаем вкладку и переходим на страницу
    page = await browser.get(
        "https://easy.co.il/list/Maintenance-and-Management-Of-Buildings"
    )

    # Включаем события сети через CDP
    await page.send(uc.cdp.network.enable())

    # Создаем обработчик для перехвата запросов с использованием метода send_and_receive
    async def intercept_requests():
        # Используем session_id из вкладки для создания сессии CDP
        session_id = page.session

        # Подписываемся на событие Network.requestWillBeSent
        await page.send(
            uc.cdp.target.set_auto_attach(
                auto_attach=True, wait_for_debugger_on_start=False, flatten=True
            )
        )

        while True:
            try:
                # Получаем события из CDP
                event = await page.send_and_receive("Network.requestWillBeSent")

                # Обрабатываем GET-запросы
                if event and "params" in event and "request" in event["params"]:
                    url = event["params"]["request"]["url"]
                    if url.startswith("https://easy.co.il/n/jsons/bizlist"):
                        try:
                            # Получаем информацию о запросе
                            request_data = event["params"]["request"]
                            # Сохраняем информацию о запросе в JSON файл с временной меткой
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                            filename = f"json/bizlist_request_{timestamp}.json"
                            with open(filename, "w", encoding="utf-8") as f:
                                json.dump(request_data, f, ensure_ascii=False, indent=2)
                            print(f"Сохранен GET-запрос в {filename}")
                        except Exception as e:
                            print(f"Ошибка при обработке запроса для {url}: {e}")

                # Обрабатываем ответы
                event = await page.send_and_receive("Network.responseReceived")
                if event and "params" in event and "response" in event["params"]:
                    url = event["params"]["response"]["url"]
                    if url.startswith("https://easy.co.il/n/jsons/bizlist"):
                        try:
                            # Получаем тело ответа
                            response_body = await page.send(
                                uc.cdp.network.get_response_body(
                                    request_id=event["params"]["requestId"]
                                )
                            )
                            json_data = json.loads(response_body.body)
                            # Сохраняем JSON в файл с временной меткой
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                            filename = f"json/bizlist_response_{timestamp}.json"
                            with open(filename, "w", encoding="utf-8") as f:
                                json.dump(json_data, f, ensure_ascii=False, indent=2)
                            print(f"Сохранен ответ JSON в {filename}")
                        except Exception as e:
                            print(f"Ошибка при получении ответа для {url}: {e}")

            except Exception as e:
                print(f"Ошибка в цикле перехвата: {e}")
                await asyncio.sleep(0.1)

    # Запускаем задачу перехвата запросов в отдельном потоке
    intercept_task = asyncio.create_task(intercept_requests())

    # Ждем загрузки страницы
    await asyncio.sleep(10)

    while True:
        # Прокручиваем страницу до конца
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(1)  # Ждем загрузки контента

        # Ищем кнопку "עוד תוצאות"
        try:
            # Используем select с ожиданием через JavaScript
            button = None
            for _ in range(5):  # Пробуем 5 раз с интервалом 1 секунда
                button = await page.select("button.next-page-button")
                if button:
                    break
                await asyncio.sleep(1)
            if not button:
                print("Кнопка 'עוד תוצאות' не найдена. Остановка.")
                break

            # Нажимаем на кнопку
            await button.click()
            print("Нажата кнопка 'עוד תוצאות'")
            await asyncio.sleep(2)  # Ждем загрузки нового контента
        except Exception as e:
            print(f"Ошибка при поиске или нажатии кнопки: {e}")
            break

    # Останавливаем задачу перехвата
    intercept_task.cancel()

    # Ждем завершения задачи
    try:
        await intercept_task
    except asyncio.CancelledError:
        pass

    # Закрываем браузер
    try:
        await browser.stop()
    except Exception as e:
        print(f"Ошибка при закрытии браузера: {e}")


# Запускаем основную функцию
if __name__ == "__main__":
    asyncio.run(main())
