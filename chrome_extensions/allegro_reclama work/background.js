// Глобальные переменные
let isAutoLoginEnabled = true;
let authCookieString = '';
let lastAuthTime = 0;
let cookiesSavedForSession = false; // Флаг - сохранены ли куки для текущей сессии
let currentSessionId = ''; // ID текущей сессии

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

        // Получаем существующие логи
        const result = await chrome.storage.local.get('extension_logs');
        let logs = result.extension_logs || [];

        // Добавляем новый лог
        logs.push(logEntry);

        // Ограничиваем количество логов
        const MAX_LOGS = 1000;
        if (logs.length > MAX_LOGS) {
            logs = logs.slice(-MAX_LOGS);
        }

        // Сохраняем обновленные логи
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
        // Определяем стандартную конфигурацию
        const defaultConfig = [
            {
                "clientId_01": "MTMwNzU2NDgwAA",
                "login_01": "wowlet",
                "password_01": "i8##-aUJ5Dviz&8"
            }
        ];

        // Сохраняем конфигурацию в хранилище
        await chrome.storage.local.set({ 'config_data': defaultConfig });
        logBackground('Конфигурация сохранена в хранилище', 'info');

        return true;
    } catch (error) {
        logBackground(`Ошибка при загрузке конфигурации: ${error.message}`, 'error');
        return false;
    }
}

// Функция редиректа на страницу логина
async function redirectToLogin(tabId) {
    try {
        await chrome.tabs.update(tabId, {
            url: 'https://allegro.com/log-in?origin_url=https%3A%2F%2Fsalescenter.allegro.com'
        });
        logBackground('Перенаправление на страницу логина');
        return true;
    } catch (error) {
        logBackground(`Ошибка при редиректе: ${error.message}`, 'error');
        return false;
    }
}

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
        // Получаем куки для разных доменов Allegro
        const allegroPlCookies = await chrome.cookies.getAll({ domain: '.allegro.pl' });
        const allegroComCookies = await chrome.cookies.getAll({ domain: '.allegro.com' });

        // Объединяем все куки
        const allCookies = [...allegroPlCookies, ...allegroComCookies];

        // Форматируем куки для использования в запросе
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

// ИСПРАВЛЕННАЯ функция для обработки событий cookies - ТОЛЬКО ОДИН РАЗ ЗА СЕССИЮ
chrome.cookies.onChanged.addListener(async (changeInfo) => {
    // Проверяем, что это установка QXLSESSID и куки не удалены
    if (changeInfo.cookie.name === 'QXLSESSID' && !changeInfo.removed) {
        const sessionId = changeInfo.cookie.value;

        // Если это новая сессия и мы еще не сохраняли куки для нее
        if (sessionId !== currentSessionId) {
            logBackground(`Обнаружена новая сессия: ${sessionId.substring(0, 10)}...`, 'info');

            // Обновляем текущую сессию и сбрасываем флаг
            currentSessionId = sessionId;
            cookiesSavedForSession = false;

            // Ждем 5 секунд для установки всех куки, затем сохраняем ОДИН РАЗ
            await delay(5000);

            if (!cookiesSavedForSession) {
                cookiesSavedForSession = true; // Устанавливаем флаг ПЕРЕД сохранением
                await saveCookiesToFile();
                logBackground('Куки сохранены для новой сессии. Повторного сохранения не будет.', 'info');
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

// Функция сохранения куки в файл
async function saveCookiesToFile() {
    try {
        // Получаем все куки для доменов Allegro
        const allegroPlCookies = await chrome.cookies.getAll({ domain: '.allegro.pl' });
        const allegroComCookies = await chrome.cookies.getAll({ domain: '.allegro.com' });

        // Объединяем все куки
        const allCookies = [...allegroPlCookies, ...allegroComCookies];

        // Форматируем куки для сохранения
        let cookieString = '';
        let cookieObj = {};

        allCookies.forEach(cookie => {
            cookieString += `${cookie.name}=${cookie.value}; `;
            cookieObj[cookie.name] = cookie.value;
        });

        // Создаем объект для сохранения
        const cookieData = {
            cookieString: cookieString.trim(),
            cookies: cookieObj,
            timestamp: new Date().toISOString(),
            formattedDate: new Date().toLocaleString(),
            sessionId: cookieObj.QXLSESSID || 'unknown'
        };

        // Преобразуем данные в JSON
        const jsonData = JSON.stringify(cookieData, null, 2);

        try {
            // Пытаемся получить данные конфигурации из chrome.storage
            const result = await chrome.storage.local.get('config_data');
            const config = result.config_data;
            let fileName = 'allegro_cookies.json';

            // Если есть конфигурация, используем clientId для формирования имени файла
            if (config && config.length > 0 && config[0].clientId_01) {
                fileName = `cookie_${config[0].clientId_01}_01.json`;
            }

            // Кодируем данные в Base64 для Data URL
            const dataUrl = `data:application/json;base64,${btoa(unescape(encodeURIComponent(jsonData)))}`;

            // Скачиваем файл
            const downloadId = await chrome.downloads.download({
                url: dataUrl,
                filename: fileName,
                saveAs: false // Без диалога сохранения
            });

            logBackground(`Куки сохранены в файл: ${fileName} (ID загрузки: ${downloadId})`, 'info');
            return {
                success: true,
                fileName: fileName,
                cookieData: cookieData
            };

        } catch (configError) {
            logBackground(`Не удалось получить конфигурацию, сохраняем с стандартным именем: ${configError.message}`, 'warn');

            // Если не удалось получить конфигурацию, используем стандартное имя файла
            const fileName = `cookie_default_${new Date().toISOString().replace(/:/g, '-')}.json`;

            // Кодируем данные в Base64 для Data URL
            const dataUrl = `data:application/json;base64,${btoa(unescape(encodeURIComponent(jsonData)))}`;

            // Скачиваем файл
            const downloadId = await chrome.downloads.download({
                url: dataUrl,
                filename: fileName,
                saveAs: false
            });

            logBackground(`Куки сохранены в файл: ${fileName} (ID загрузки: ${downloadId})`, 'info');
            return {
                success: true,
                fileName: fileName,
                cookieData: cookieData
            };
        }
    } catch (error) {
        logBackground(`Ошибка при сохранении куки в файл: ${error.message}`, 'error');
        return {
            success: false,
            error: error.message
        };
    }
}

// Слушатель обновления вкладок
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.url && tab.url.includes('allegro')) {
        const isLoggedIn = await checkLoginStatus();
        if (!isLoggedIn && isAutoLoginEnabled) {
            logBackground('Начинаем процесс логина...', 'info');
            await redirectToLogin(tabId);
        } else if (isLoggedIn) {
            logBackground('Пользователь авторизован', 'info');
        }
    }
});

// Основной обработчик сообщений
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    // Проверка логина
    if (message.action === "checkLogin") {
        checkLoginStatus().then(isLoggedIn => {
            if (!isLoggedIn && isAutoLoginEnabled) {
                redirectToLogin(sender.tab.id).then(() => {
                    sendResponse({ status: 'redirecting' });
                });
            } else {
                sendResponse({ status: isLoggedIn ? 'logged_in' : 'not_logged_in' });
            }
        });
        return true;
    }

    // Обработчик для сохранения куки в файл (ручное сохранение отключено)
    if (message.action === "saveCookies") {
        // Ручное сохранение отключено
        sendResponse({
            success: false,
            error: "Ручное сохранение отключено. Куки сохраняются автоматически один раз за сессию."
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