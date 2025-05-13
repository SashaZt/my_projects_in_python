// Функция для логирования
function sendLog(message, type = 'info') {
    console.log(`[Login][${type}]`, message);
    chrome.runtime.sendMessage({
        action: "log",
        message: `[Login] ${message}`,
        type: type
    }).catch(() => { });
}

// Функция ожидания элемента с повторными попытками
async function waitForElement(selector, timeout = 10000, maxAttempts = 3) {
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
            return await waitForElementAttempt(selector, timeout);
        } catch (error) {
            sendLog(`Попытка ${attempt}/${maxAttempts} найти ${selector}: ${error.message}`, 'warn');
            if (attempt === maxAttempts) {
                throw error;
            }
            // Ждем перед следующей попыткой
            await delay(1000);
        }
    }
}

// Вспомогательная функция для waitForElement
async function waitForElementAttempt(selector, timeout) {
    return new Promise((resolve, reject) => {
        const startTime = Date.now();

        const checkElement = () => {
            const element = document.querySelector(selector);
            if (element) {
                resolve(element);
                return;
            }

            if (Date.now() - startTime >= timeout) {
                reject(new Error(`Элемент ${selector} не найден после ${timeout}мс`));
                return;
            }

            requestAnimationFrame(checkElement);
        };

        checkElement();
    });
}

// Функция для симуляции пользовательского ввода
function simulateUserInput(element, value) {
    element.focus();
    element.value = value;
    const events = ['input', 'change', 'blur'];
    events.forEach(eventName => {
        element.dispatchEvent(new Event(eventName, { bubbles: true }));
    });

    // Дополнительно проверяем, что значение действительно установлено
    if (element.value !== value) {
        sendLog(`Предупреждение: Не удалось установить значение в поле (${element.value} != ${value})`, 'warn');
        // Пробуем еще раз прямым присваиванием
        setTimeout(() => {
            element.value = value;
            element.dispatchEvent(new Event('change', { bubbles: true }));
        }, 100);
    }
}

// Задержка
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Основная функция автологина
async function performLogin() {
    try {
        // Получаем конфигурацию из storage
        const result = await chrome.storage.local.get('config_data');
        const config = result.config_data;

        if (config && config.length > 0) {
            const account = config[0];
            const username = account.login_01;
            const password = account.password_01;

            sendLog(`Начинаем процесс автологина для магазина: ${username}`);
            await loginWithCredentials(username, password);
        } else {
            sendLog('Не удалось получить данные для автологина из хранилища', 'warn');
            // Используем дефолтные данные
            await loginWithCredentials("wowlet", "i8##-aUJ5Dviz&8");
        }
    } catch (error) {
        sendLog(`Ошибка при автологине: ${error.message}`, 'error');
        throw error;
    }
}

// Функция логина с указанными учетными данными
async function loginWithCredentials(username, password) {
    try {
        // Проверяем, что мы на странице логина
        if (!window.location.href.includes('/log-in')) {
            sendLog('Не находимся на странице логина, переход не будет выполнен', 'warn');
            return;
        }

        sendLog('Ждем загрузки формы логина...');

        // Используем точные селекторы для поля логина
        let loginInput;
        try {
            loginInput = await waitForElement('input[name="login"]');
            sendLog('Найден элемент ввода логина');
        } catch (error) {
            sendLog('Не удалось найти поле для ввода логина', 'error');
            throw error;
        }

        // Получаем поле пароля
        let passwordInput;
        try {
            passwordInput = await waitForElement('input[type="password"]');
            sendLog('Найден элемент ввода пароля');
        } catch (error) {
            sendLog('Не удалось найти поле для ввода пароля', 'error');
            throw error;
        }

        // Ищем кнопку отправки формы
        let submitButton;
        try {
            submitButton = await waitForElement('button[type="submit"]');
            sendLog('Найдена кнопка отправки формы');
        } catch (error) {
            sendLog('Не удалось найти кнопку отправки формы', 'error');
            throw error;
        }

        sendLog('Элементы формы найдены, заполняем данные');

        await delay(500);

        // Эмулируем ввод
        simulateUserInput(loginInput, username);
        await delay(500);
        simulateUserInput(passwordInput, password);
        await delay(500);

        // Отправляем форму
        sendLog('Отправляем форму авторизации');
        submitButton.click();

        // Ждем редиректа после успешного логина
        sendLog('Ожидаем редиректа после логина');
        await waitForRedirect();

    } catch (error) {
        sendLog(`Ошибка при попытке логина: ${error.message}`, 'error');
        throw error;
    }
}

// Функция ожидания редиректа
async function waitForRedirect(timeout = 15000) {
    const startTime = Date.now();
    const startUrl = window.location.href;

    return new Promise((resolve, reject) => {
        const checkRedirect = () => {
            // Проверяем, изменился ли URL
            if (window.location.href !== startUrl) {
                sendLog(`Успешный редирект на ${window.location.href}`, 'info');
                resolve();
                return;
            }

            // Проверяем, есть ли сообщение об ошибке
            const errorElement = document.querySelector('[data-testid="login-error"]');
            if (errorElement) {
                const errorMessage = errorElement.textContent.trim();
                sendLog(`Обнаружена ошибка логина: ${errorMessage}`, 'error');
                reject(new Error(`Ошибка логина: ${errorMessage}`));
                return;
            }

            // Проверяем таймаут
            if (Date.now() - startTime >= timeout) {
                sendLog('Таймаут при ожидании редиректа', 'warn');
                // В данном случае мы не считаем это ошибкой, так как страница может просто загружаться
                resolve();
                return;
            }

            // Продолжаем проверку
            setTimeout(checkRedirect, 500);
        };

        // Начинаем проверку
        checkRedirect();
    });
}

// Запускаем автологин при загрузке страницы
if (window.location.href.includes('/log-in')) {
    sendLog('Обнаружена страница логина');

    // Функция для проверки готовности страницы
    function checkPageReady() {
        // Если DOM уже загружен
        if (document.readyState === 'complete' || document.readyState === 'interactive') {
            sendLog('Страница готова, ждем 2 секунды перед запуском логина');
            setTimeout(performLogin, 2000);
        } else {
            // Иначе ждем загрузки
            sendLog('Ожидаем загрузки страницы');
            document.addEventListener('DOMContentLoaded', () => {
                sendLog('DOM загружен, ждем 2 секунды перед запуском логина');
                setTimeout(performLogin, 2000);
            });
        }
    }

    // Даем странице время полностью загрузиться
    setTimeout(checkPageReady, 1000);
}

// Слушатель сообщений
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "performLogin") {
        sendLog('Получен запрос на выполнение логина');
        performLogin()
            .then(() => {
                sendLog('Логин выполнен успешно');
                sendResponse({ success: true });
            })
            .catch(error => {
                sendLog(`Ошибка при выполнении логина: ${error.message}`, 'error');
                sendResponse({ success: false, error: error.message });
            });
        return true; // Удерживаем соединение для асинхронного ответа
    }
});

// Проверяем, не застрял ли процесс логина
setTimeout(async () => {
    try {
        if (window.location.href.includes('/log-in')) {
            // Проверяем, есть ли форма логина
            const loginForm = document.querySelector('form');
            if (loginForm) {
                // Если форма всё еще на странице, попробуем ещё раз выполнить логин
                sendLog('Форма логина всё еще на странице, пробуем выполнить логин повторно', 'warn');
                await performLogin();
            }
        }
    } catch (error) {
        sendLog(`Ошибка при проверке состояния логина: ${error.message}`, 'error');
    }
}, 20000); // Проверка через 20 секунд после загрузки страницы