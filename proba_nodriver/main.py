import asyncio
import nodriver as uc


async def main():
    # Открываем браузер
    browser = (
        await uc.start()
    )  # Добавьте параметр headless=True, если не хотите видеть браузер
    # Переходим на страницу
    page = await browser.get("https://hotline.ua/")
    element_find = await page.wait_for(
        selector="#autosuggest > div:nth-child(1) > input[type=text]", timeout=15
    )
    


    content = await page.get_content()

    # Получаем содержимое   я страницы
    # content = await page.evaluate("() => document.documentElement.outerHTML")

    # Проверяем, что содержимое не None
    if content:
        # Сохраняем в файл sitemap.xml
        with open("sitemap.html", "w", encoding="utf-8") as f:
            f.write(content)
    else:
        print("Контент не найден.")

    # Закрываем страницу
    await page.close()


if __name__ == "__main__":
    # since asyncio.run never worked (for me)
    uc.loop().run_until_complete(main())
