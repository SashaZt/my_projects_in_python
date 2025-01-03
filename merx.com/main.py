import asyncio

from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as playwright:
        # Запускаем браузер
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(
            bypass_csp=True,
            java_script_enabled=True,
            permissions=["geolocation"],
            device_scale_factor=1.0,
            has_touch=True,
            ignore_https_errors=True,
        )

        # Создаем новую страницу
        page = await context.new_page()

        # Переходим по URL
        await page.goto("https://www.merx.com/")

        # Ждем полной загрузки страницы
        await page.wait_for_load_state("networkidle")

        # Находим ссылку на кнопку "Login" и нажимаем её
        await page.click("a.mets-command-button.loginButton#header_btnLogin")

        # Ждем полной загрузки страницы после нажатия кнопки
        await page.wait_for_load_state("networkidle")

        # Находим поле для ввода логина и вводим значение
        await page.fill("input#j_username", "max@mldrl.com")

        # Находим поле для ввода пароля и вводим значение
        await page.fill("input#j_password", "MERx(6379)")

        # Находим кнопку "Login" и нажимаем её
        await page.click("button#loginButton")

        # Ждем 60 секунд
        await page.wait_for_timeout(100000)
        # Находим элемент "My Account" по title и нажимаем его
        await page.click('a[title="My Account"]')

        # Ждем появления выпадающего списка
        await page.wait_for_selector('a[title="Logout"]')

        # Находим элемент "Logout" по title и нажимаем его
        await page.click('a[title="Logout"]')

        # Ждем 5 секунд
        await page.wait_for_timeout(50000)

        # Закрываем браузер
        await browser.close()


# Запускаем асинхронный код
asyncio.run(main())
