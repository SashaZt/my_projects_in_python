// Данные для автологина
const LOGIN_DATA = {
    username: 'OficjalnyResteq',
    password: 'If[rjytv1'
};

// Функция для логирования
function sendLog(message, type = 'info') {
    console.log(`[Login][${type}]`, message);
    chrome.runtime.sendMessage({
        action: "log",
        message: `[Login] ${message}`,
        type: type
    }).catch(() => { });
}

// Функция ожидания элемента
async function waitForElement(selector, timeout = 5000) {
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
}

// Задержка
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Основная функция автологина
async function performLogin() {
    try {
        sendLog('Начинаем процесс автологина');

        // Ждем загрузки формы
        const loginInput = await waitForElement('input[name="login"][autocomplete="username"]');
        const passwordInput = await waitForElement('input[name="password"][autocomplete="current-password"]');
        const submitButton = await waitForElement('button[data-testid="login-btn"]');

        sendLog('Элементы формы найдены, заполняем данные');

        // Эмулируем ввод
        simulateUserInput(loginInput, LOGIN_DATA.username);
        await delay(500);
        simulateUserInput(passwordInput, LOGIN_DATA.password);
        await delay(500);

        // Отправляем форму
        sendLog('Отправляем форму авторизации');
        submitButton.click();

    } catch (error) {
        sendLog(`Ошибка при автологине: ${error.message}`, 'error');
        throw error;
    }
}

// Запускаем автологин при загрузке страницы
if (window.location.href.includes('/log-in')) {
    sendLog('Обнаружена страница логина');

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(performLogin, 1000);
        });
    } else {
        setTimeout(performLogin, 1000);
    }
}

// Слушатель сообщений
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "performLogin") {
        performLogin()
            .then(() => sendResponse({ success: true }))
            .catch(error => sendResponse({ success: false, error: error.message }));
        return true;
    }
});