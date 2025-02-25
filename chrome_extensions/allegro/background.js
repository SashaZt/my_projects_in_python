// Глобальные переменные
let isAutoLoginEnabled = true;
let accumulatedOffers = [];
const processedOfferIds = new Set();
let isProcessing = false;
import { SHOPS_CONFIG, URLS } from './config.js';

// Добавляем глобальные переменные для управления магазинами
let currentShopIndex = 0;
let isProcessingShops = false;

// Настройки планировщика
let schedulerSettings = {
    enabled: false,
    time: "08:00",
    days: [],
    lastRun: null,
    nextRun: null
};

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

    // Загружаем настройки планировщика
    await loadSchedulerSettings();
});

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

// Обработка запросов офферов
async function processOffersRequest(details) {
    if (isProcessing) return;

    try {
        isProcessing = true;
        const headers = {};
        details.requestHeaders.forEach(header => {
            headers[header.name] = header.value;
        });

        const response = await fetch(details.url, { headers });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        if (!data || !data.offers) return;

        const newOffers = data.offers.filter(offer => !processedOfferIds.has(offer.id));
        if (newOffers.length === 0) return;

        newOffers.forEach(offer => processedOfferIds.add(offer.id));

        const processedData = newOffers.map(offer => ({
            id: offer.id,
            name: offer.name,
            stats: {
                watchersCount: offer.stats?.watchersCount,
                visitsCount: offer.stats?.visitsCount
            },
            stock: {
                sold: offer.stock?.sold
            }
        }));

        accumulatedOffers = [...accumulatedOffers, ...processedData];

        chrome.runtime.sendMessage({
            action: "statsUpdate",
            stats: {
                accumulated: accumulatedOffers.length,
                new: newOffers.length
            }
        }).catch(() => { });

        logBackground(`Added ${newOffers.length} new offers (Total: ${accumulatedOffers.length})`);
    } catch (error) {
        logBackground(`Error processing request: ${error.message}`, 'error');
    } finally {
        isProcessing = false;
    }
}

// Функция для автоматической загрузки экспортированных данных
async function autoDownloadExportedData(data, fileName) {
    try {
        // Преобразуем данные в JSON и затем в Base64
        const jsonString = JSON.stringify(data, null, 2);

        // Кодируем данные в формат Data URL
        // Это альтернатива URL.createObjectURL, который не работает в сервис-воркере
        const dataUrl = 'data:application/json;base64,' + btoa(unescape(encodeURIComponent(jsonString)));

        // Скачиваем файл
        const downloadId = await chrome.downloads.download({
            url: dataUrl,
            filename: fileName,
            saveAs: false
        });

        logBackground(`Данные автоматически сохранены в файл: ${fileName} (ID: ${downloadId})`);
        return true;
    } catch (error) {
        logBackground(`Ошибка при автоматическом сохранении: ${error.message}`, 'error');

        // Если ошибка возникла из-за слишком большого размера data URL, разделим данные на части
        try {
            if (error.message.includes('too large') || error.message.includes('size') || data.length > 1000) {
                logBackground('Попытка разделить данные на части для сохранения', 'info');

                // Разделим данные на части по 500 элементов
                const chunks = [];
                for (let i = 0; i < data.length; i += 500) {
                    chunks.push(data.slice(i, i + 500));
                }

                // Скачиваем каждую часть отдельно
                for (let i = 0; i < chunks.length; i++) {
                    const chunkFileName = fileName.replace('.json', `_part${i + 1}.json`);
                    const chunkJson = JSON.stringify(chunks[i], null, 2);
                    const chunkDataUrl = 'data:application/json;base64,' + btoa(unescape(encodeURIComponent(chunkJson)));

                    const chunkDownloadId = await chrome.downloads.download({
                        url: chunkDataUrl,
                        filename: chunkFileName,
                        saveAs: false
                    });

                    logBackground(`Часть ${i + 1} сохранена в файл: ${chunkFileName} (ID: ${chunkDownloadId})`);
                }

                return true;
            }
        } catch (chunkedError) {
            logBackground(`Ошибка при попытке разделить данные: ${chunkedError.message}`, 'error');
        }

        // Если все методы не сработали, сохраняем данные в локальное хранилище
        try {
            const storageKey = `backup_export_${new Date().toISOString().replace(/[:.]/g, '_')}`;
            await chrome.storage.local.set({
                [storageKey]: {
                    data: data,
                    timestamp: new Date().toISOString(),
                    fileName: fileName
                }
            });
            logBackground(`Не удалось скачать файл, но данные сохранены в локальное хранилище с ключом ${storageKey}`, 'warn');
        } catch (storageError) {
            logBackground(`Также не удалось сохранить в хранилище: ${storageError.message}`, 'error');
        }

        return false;
    }
}

// Функция экспорта офферов
async function exportOffers() {
    if (accumulatedOffers.length === 0) {
        // Если нет данных, но мы в режиме обработки магазинов, переходим к следующему
        if (isProcessingShops) {
            logBackground('Нет данных для экспорта, переходим к следующему магазину');
            currentShopIndex++;

            if (currentShopIndex < SHOPS_CONFIG.length) {
                // Переходим к следующему магазину
                processNextShop();
            } else {
                logBackground('Обработка всех магазинов завершена');
                isProcessingShops = false;
            }
        }

        return {
            success: false,
            message: "No offers to export"
        };
    }

    try {
        const storage = await chrome.storage.local.get('currentShop');
        const fileName = storage.currentShop?.fileName || 'default';
        const currentDate = new Date().toISOString().split('T')[0]; // Получит только дату, например "2025-02-24"

        const result = {
            success: true,
            count: accumulatedOffers.length,
            data: accumulatedOffers,
            fileName: `${fileName}_${currentDate}.json`
        };

        logBackground(`Prepared ${accumulatedOffers.length} offers for export for shop ${fileName}`);

        // Создаем копию данных перед тем, как очистить массив
        const offersToExport = [...accumulatedOffers];

        // Сохраняем данные в локальное хранилище
        try {
            await chrome.storage.local.set({
                [`export_${fileName}_${currentDate}`]: {
                    data: offersToExport,
                    timestamp: new Date().toISOString(),
                    fileName: `${fileName}_${currentDate}.json`
                }
            });
            logBackground(`Данные сохранены в локальное хранилище`);

            // Автоматически скачиваем данные
            await autoDownloadExportedData(offersToExport, `${fileName}_${currentDate}.json`);
        } catch (storageError) {
            logBackground(`Ошибка сохранения в хранилище: ${storageError.message}`, 'error');
        }

        // Очищаем массив после экспорта
        accumulatedOffers = [];
        processedOfferIds.clear();

        // После успешного экспорта
        setTimeout(async () => {
            if (isProcessingShops) {
                logBackground('Процесс сбора данных для текущего магазина завершен');

                // Увеличиваем индекс для следующего магазина
                currentShopIndex++;

                // Если есть следующий магазин
                if (currentShopIndex < SHOPS_CONFIG.length) {
                    logBackground('Переход к следующему магазину');

                    // Находим активную вкладку
                    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
                    if (tabs[0]) {
                        // Сначала делаем logout
                        await chrome.tabs.update(tabs[0].id, {
                            url: URLS.LOGOUT_URL
                        });

                        // После logout скрипт login.js подхватит следующий магазин
                        const nextShop = SHOPS_CONFIG[currentShopIndex];
                        await chrome.storage.local.set({
                            currentShop: nextShop,
                            isProcessingShops: true
                        });

                        logBackground(`Подготовлен следующий магазин: ${nextShop.username}`);
                    } else {
                        // Если активной вкладки нет, создаем новую
                        const newTab = await chrome.tabs.create({
                            url: URLS.LOGOUT_URL,
                            active: true
                        });
                        logBackground(`Создана новая вкладка для logout`);

                        // После logout скрипт login.js подхватит следующий магазин
                        const nextShop = SHOPS_CONFIG[currentShopIndex];
                        await chrome.storage.local.set({
                            currentShop: nextShop,
                            isProcessingShops: true
                        });

                        logBackground(`Подготовлен следующий магазин: ${nextShop.username}`);
                    }
                } else {
                    logBackground('Обработка всех магазинов завершена');
                    isProcessingShops = false;

                    // Делаем выход после завершения всех магазинов
                    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
                    if (tabs[0]) {
                        await chrome.tabs.update(tabs[0].id, {
                            url: URLS.COMPLETE_URL
                        });
                        logBackground('Выполнен выход после завершения всех магазинов');
                    }
                }
            }
        }, 5000);

        return result;
    } catch (error) {
        logBackground(`Export error: ${error.message}`, 'error');
        return {
            success: false,
            error: error.message
        };
    }
}

// Функция для обработки следующего магазина
async function processNextShop() {
    if (currentShopIndex >= SHOPS_CONFIG.length) {
        logBackground('Обработка всех магазинов завершена');
        isProcessingShops = false;
        return;
    }

    const currentShop = SHOPS_CONFIG[currentShopIndex];
    logBackground(`Начинаем обработку магазина: ${currentShop.username}`);

    try {
        // Сохраняем текущий магазин в storage
        await chrome.storage.local.set({
            currentShop,
            isProcessingShops: true
        });

        // Находим активную вкладку
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tabs[0]) {
            // Если активной вкладки нет, создаем новую
            await chrome.tabs.create({
                url: URLS.LOGIN_URL,
                active: true
            });
        } else {
            // Если есть активная вкладка, используем её
            await chrome.tabs.update(tabs[0].id, {
                url: URLS.LOGIN_URL
            });
        }

        logBackground(`Подготовлена обработка для магазина ${currentShop.username}`);
    } catch (error) {
        logBackground(`Ошибка при обработке магазина ${currentShop.username}: ${error.message}`, 'error');
        // При ошибке переходим к следующему магазину
        currentShopIndex++;
        setTimeout(processNextShop, 5000);
    }
}

// Функции планировщика
async function loadSchedulerSettings() {
    try {
        const result = await chrome.storage.local.get('schedulerSettings');
        if (result.schedulerSettings) {
            schedulerSettings = result.schedulerSettings;
            logBackground('Загружены настройки планировщика');
            logBackground(`Планировщик: ${schedulerSettings.enabled ? 'Включен' : 'Выключен'}`);
            logBackground(`Время запуска: ${schedulerSettings.time}`);
            logBackground(`Дни запуска: ${schedulerSettings.days.join(', ')}`);
            logBackground(`Следующий запуск: ${schedulerSettings.nextRun ? new Date(schedulerSettings.nextRun).toLocaleString() : 'не задан'}`);

            updateNextRun();
        } else {
            // Если настроек нет, создаем начальные настройки
            schedulerSettings = {
                enabled: true,  // По умолчанию включаем планировщик
                time: "08:00",
                days: [1, 2, 3, 4, 5], // По умолчанию пн-пт
                lastRun: null,
                nextRun: null
            };
            await saveSchedulerSettings(schedulerSettings);
        }
    } catch (error) {
        logBackground(`Error loading scheduler settings: ${error.message}`, 'error');
    }
}

// Функция для сохранения настроек
async function saveSchedulerSettings(settings) {
    try {
        // Объединяем существующие настройки с новыми
        schedulerSettings = { ...schedulerSettings, ...settings };

        // Сохраняем в локальное хранилище
        await chrome.storage.local.set({ 'schedulerSettings': schedulerSettings });

        // Обновляем время следующего запуска
        updateNextRun();

        // Сохраняем обновленные настройки еще раз (с обновленным nextRun)
        await chrome.storage.local.set({ 'schedulerSettings': schedulerSettings });

        logBackground('Настройки планировщика сохранены');
        return { success: true };
    } catch (error) {
        logBackground(`Error saving scheduler settings: ${error.message}`, 'error');
        return { success: false, error: error.message };
    }
}

// Функция обновления времени следующего запуска
function updateNextRun() {
    if (!schedulerSettings.enabled || !schedulerSettings.time || !schedulerSettings.days.length) {
        schedulerSettings.nextRun = null;
        return;
    }

    const now = new Date();
    const [hours, minutes] = schedulerSettings.time.split(':').map(Number);

    // Создаем дату для сегодняшнего дня с указанным временем
    let nextRun = new Date(now);
    nextRun.setHours(hours, minutes, 0, 0);

    // Если указанное время уже прошло, переносим на следующий день
    if (nextRun <= now) {
        nextRun.setDate(nextRun.getDate() + 1);
    }

    // Проверяем, входит ли день недели в выбранные дни
    const dayOfWeek = nextRun.getDay(); // 0 = воскресенье, 1 = понедельник и т.д.

    if (!schedulerSettings.days.includes(dayOfWeek)) {
        // Если текущий день не входит в выбранные, ищем ближайший подходящий
        let daysToAdd = 1;
        let currentDayToCheck = (dayOfWeek + 1) % 7;

        while (!schedulerSettings.days.includes(currentDayToCheck) && daysToAdd < 7) {
            daysToAdd++;
            currentDayToCheck = (currentDayToCheck + 1) % 7;
        }

        // Добавляем нужное количество дней
        nextRun.setDate(nextRun.getDate() + daysToAdd);
    }

    logBackground(`Следующий запуск запланирован на: ${nextRun.toLocaleString()}`);
    schedulerSettings.nextRun = nextRun.toISOString();
}

async function startScheduledRun() {
    try {
        logBackground('Начало запланированного запуска');

        // Инициализируем процесс
        currentShopIndex = 0;
        isProcessingShops = true;
        accumulatedOffers = [];
        processedOfferIds.clear();

        // Сохраняем первый магазин в storage
        const currentShop = SHOPS_CONFIG[currentShopIndex];
        await chrome.storage.local.set({
            currentShop,
            isProcessingShops: true
        });

        logBackground(`Подготовка к обработке магазина: ${currentShop.username}`);

        // Проверяем, есть ли активные вкладки с allegro
        const allegroTabs = await chrome.tabs.query({ url: "*://*.allegro.com/*" });

        if (allegroTabs.length > 0) {
            // Используем существующую вкладку
            await chrome.tabs.update(allegroTabs[0].id, {
                url: URLS.LOGIN_URL,
                active: true
            });
            logBackground('Используем существующую вкладку для начала процесса');
        } else {
            // Создаем новую вкладку
            const tab = await chrome.tabs.create({
                url: URLS.LOGIN_URL,
                active: true
            });
            logBackground('Создана новая вкладка для начала процесса');
        }

    } catch (error) {
        logBackground(`Error in scheduled run: ${error.message}`, 'error');
        isProcessingShops = false;
    }
}

// Функция проверки необходимости запуска
async function checkScheduledRun() {
    try {
        if (!schedulerSettings.enabled || !schedulerSettings.nextRun) {
            return;
        }

        const now = new Date();
        const nextRun = new Date(schedulerSettings.nextRun);

        // Упрощаем проверку - сравниваем даты и часы:минуты
        const nowHoursMinutes = now.getHours() * 60 + now.getMinutes();
        const nextRunHoursMinutes = nextRun.getHours() * 60 + nextRun.getMinutes();

        // Форматируем для логов
        const nowFormatted = `${now.toLocaleDateString()} ${now.getHours()}:${now.getMinutes().toString().padStart(2, '0')}`;
        const nextRunFormatted = `${nextRun.toLocaleDateString()} ${nextRun.getHours()}:${nextRun.getMinutes().toString().padStart(2, '0')}`;

        logBackground(`Проверка планировщика: Сейчас: ${nowFormatted}, Запланировано: ${nextRunFormatted}`, 'debug');

        // Проверяем, что сегодня нужный день и время соответствует запланированному
        const isSameDate =
            now.getFullYear() === nextRun.getFullYear() &&
            now.getMonth() === nextRun.getMonth() &&
            now.getDate() === nextRun.getDate();

        const isTimeMatched = Math.abs(nowHoursMinutes - nextRunHoursMinutes) <= 2; // Погрешность ±2 минуты

        if (isSameDate && isTimeMatched) {
            logBackground('Наступило время запланированного запуска!');

            // Проверяем, не запускали ли мы уже сегодня
            const lastRunDate = schedulerSettings.lastRun ? new Date(schedulerSettings.lastRun) : null;
            const isAlreadyRun = lastRunDate &&
                lastRunDate.getFullYear() === now.getFullYear() &&
                lastRunDate.getMonth() === now.getMonth() &&
                lastRunDate.getDate() === now.getDate();

            if (isAlreadyRun) {
                logBackground('Уже был запуск сегодня, пропускаем');
                return;
            }

            // Запускаем запланированный процесс
            await startScheduledRun();

            // Обновляем время последнего запуска
            schedulerSettings.lastRun = now.toISOString();

            // Обновляем время следующего запуска
            updateNextRun();

            // Сохраняем обновленные настройки
            await saveSchedulerSettings({});
        }
    } catch (error) {
        logBackground(`Ошибка при проверке планировщика: ${error.message}`, 'error');
    }
}

// Слушатель изменения куки
chrome.cookies.onChanged.addListener(async (changeInfo) => {
    if (changeInfo.cookie.name === 'QXLSESSID') {
        if (changeInfo.removed) {
            logBackground('Сессия завершена, куки удалены');
        } else {
            logBackground('Новая сессия установлена');
        }
    }
});

// Слушатель обновления вкладок
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' &&
        tab.url &&
        tab.url.includes('allegro') &&
        !tab.url.includes('/login')) {

        const isLoggedIn = await checkLoginStatus();
        if (!isLoggedIn && isAutoLoginEnabled) {
            logBackground('Обнаружена неавторизованная сессия, начинаем процесс логина');
            await redirectToLogin(tabId);
        }
    }
});

// Слушатель веб-запросов
chrome.webRequest.onBeforeSendHeaders.addListener(
    async function (details) {
        if (details.url.includes('edge.salescenter.allegro.com/sale/offers') &&
            !details.url.includes('/stats')) {
            processOffersRequest(details);
        }
    },
    { urls: ["*://edge.salescenter.allegro.com/*"] },
    ["requestHeaders"]
);

// Создание будильника для проверки планировщика
chrome.alarms.create('schedulerCheck', {
    periodInMinutes: 1 // Проверяем каждую минуту
});

// Слушатель для будильника
chrome.alarms.onAlarm.addListener((alarm) => {
    if (alarm.name === 'schedulerCheck') {
        checkScheduledRun();
    }
});

// Основной обработчик сообщений
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "startShopsProcessing") {
        currentShopIndex = 0;
        processNextShop();
        sendResponse({ status: "started" });
        return true;
    }
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

    if (message.action === "exportOffers") {
        exportOffers().then(result => {
            sendResponse(result);
        });
        return true;
    }

    if (message.action === "getStats") {
        sendResponse({
            accumulated: accumulatedOffers.length,
            uniqueIds: processedOfferIds.size
        });
        return true;
    }

    if (message.action === "getSchedulerSettings") {
        sendResponse(schedulerSettings);
        return true;
    }

    if (message.action === "saveSchedulerSettings") {
        saveSchedulerSettings(message.settings).then(result => {
            sendResponse(result);
        });
        return true;
    }

    return false;
});

// Инициализация планировщика при запуске расширения
(async function initScheduler() {
    await loadSchedulerSettings();

    // Проверяем, нужно ли запустить планировщик сразу
    await checkScheduledRun();

    logBackground('Планировщик инициализирован');
})();

// Регистрируем обработчик для событий загрузки
chrome.downloads.onChanged.addListener((downloadDelta) => {
    if (downloadDelta.state && downloadDelta.state.current === 'complete') {
        logBackground(`Загрузка ${downloadDelta.id} завершена успешно`);
    }
    else if (downloadDelta.error) {
        logBackground(`Ошибка загрузки ${downloadDelta.id}: ${downloadDelta.error.current}`, 'error');
    }
});