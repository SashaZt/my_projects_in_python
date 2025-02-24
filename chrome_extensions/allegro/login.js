// Функция для получения данных текущего магазина
async function getCurrentShop() {
    return new Promise((resolve) => {
        chrome.storage.local.get(['currentShop', 'isProcessingShops'], (result) => {
            resolve(result);
        });
    });
}

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
        // Получаем данные текущего магазина
        const { currentShop, isProcessingShops } = await getCurrentShop();

        if (!currentShop || !isProcessingShops) {
            sendLog('Нет данных для автологина', 'warn');

            // Получаем конфигурацию из импорта
            try {
                const { SHOPS_CONFIG } = await import('./config.js');

                if (SHOPS_CONFIG && SHOPS_CONFIG.length > 0) {
                    // Используем данные из конфига
                    const defaultShop = SHOPS_CONFIG[0];
                    sendLog(`Используем данные из конфига для магазина ${defaultShop.username}`, 'info');
                    await loginWithCredentials(defaultShop.username, defaultShop.password);
                    return;
                }
            } catch (importError) {
                sendLog(`Не удалось импортировать конфигурацию: ${importError.message}`, 'error');
            }

            return;
        }

        sendLog(`Начинаем процесс автологина для магазина: ${currentShop.username}`);
        await loginWithCredentials(currentShop.username, currentShop.password);

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

        // Ждем загрузки формы с повторными попытками
        const loginInput = await waitForElement('input[name="login"][autocomplete="username"]');
        const passwordInput = await waitForElement('input[name="password"][autocomplete="current-password"]');
        const submitButton = await waitForElement('button[data-testid="login-btn"]');

        sendLog('Элементы формы найдены, заполняем данные');

        // Эмулируем ввод
        simulateUserInput(loginInput, username);
        await delay(500);
        simulateUserInput(passwordInput, password);
        await delay(500);

        // Проверяем, что данные действительно введены
        if (loginInput.value !== username || passwordInput.value !== password) {
            sendLog('Предупреждение: данные не были корректно введены в форму', 'warn');
            // Повторно пытаемся установить значения
            loginInput.value = username;
            passwordInput.value = password;
            await delay(300);
        }

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
            sendLog('Страница готова, ждем 1 секунду перед запуском логина');
            setTimeout(performLogin, 1000);
        } else {
            // Иначе ждем загрузки
            sendLog('Ожидаем загрузки страницы');
            document.addEventListener('DOMContentLoaded', () => {
                sendLog('DOM загружен, ждем 1 секунду перед запуском логина');
                setTimeout(performLogin, 1000);
            });
        }
    }

    // Даем странице время полностью загрузиться
    setTimeout(checkPageReady, 500);
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
            const loginForm = document.querySelector('form[data-testid="login-form"]');
            if (loginForm) {
                // Если форма всё еще на странице, попробуем ещё раз выполнить логин
                sendLog('Форма логина всё еще на странице, пробуем выполнить логин повторно', 'warn');
                await performLogin();
            }
        }
    } catch (error) {
        sendLog(`Ошибка при проверке состояния логина: ${error.message}`, 'error');
    }
}, 15000); // Проверка через 15 секунд после загрузки страницы