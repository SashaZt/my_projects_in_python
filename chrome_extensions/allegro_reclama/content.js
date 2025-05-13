// Флаг для отслеживания состояния авторизации
let wasLoggedIn = false;

function sendLog(message, type = 'info') {
    console.log(`[Content][${type}]`, message);
    chrome.runtime.sendMessage({
        action: "log",
        message: `[Content] ${message}`,
        type: type
    }).catch(() => { }); // Игнорируем ошибки отправки логов
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

sendLog('Скрипт контента загружен и инициализирован');

// Следим за изменениями URL
let lastUrl = location.href;
new MutationObserver(() => {
    if (location.href !== lastUrl) {
        lastUrl = location.href;

        // Если это страница логина, сообщаем background script
        if (location.href.includes('/log-in')) {
            sendLog('Обнаружена страница логина', 'info');
        }
    }
}).observe(document, { subtree: true, childList: true });

// Функция для проверки куки QXLSESSID
function checkSession() {
    const isLoggedIn = document.cookie.includes('QXLSESSID');

    // Отправляем сообщение только при изменении состояния авторизации
    if (isLoggedIn && !wasLoggedIn) {
        wasLoggedIn = true;
        sendLog('Обнаружена успешная авторизация', 'info');

        chrome.runtime.sendMessage({
            action: "loginDetected"
        });
    } else if (!isLoggedIn && wasLoggedIn) {
        wasLoggedIn = false;
        sendLog('Выход из аккаунта обнаружен', 'info');
    }
}

// Проверяем сессию при загрузке и периодически
window.addEventListener('load', function () {
    // Проверяем сессию при загрузке
    checkSession();

    // Проверяем сессию каждые 10 секунд
    setInterval(checkSession, 10000);
});

// Обработчик сообщений
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "ping") {
        sendResponse({ status: "pong" });
    }
    return true;
});