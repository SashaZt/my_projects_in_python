// Хранилище для накопления офферов
let accumulatedOffers = [];
const processedOfferIds = new Set();
let isProcessing = false;

function logBackground(message, type = 'info') {
    console.log(`[Background][${type}]`, message);
    if (type !== 'debug') {
        chrome.runtime.sendMessage({
            action: "log",
            message: `[Background] ${message}`,
            type: type
        }).catch(() => { });
    }
}

// Функция для экспорта данных
async function exportOffers() {
    if (accumulatedOffers.length === 0) {
        return {
            success: false,
            message: "No offers to export"
        };
    }

    try {
        // Отправляем данные, а создание и скачивание файла будет в popup
        const result = {
            success: true,
            count: accumulatedOffers.length,
            data: accumulatedOffers
        };

        logBackground(`Prepared ${accumulatedOffers.length} offers for export`);

        // Очищаем накопленные данные только после успешного экспорта
        const count = accumulatedOffers.length;
        accumulatedOffers = [];
        processedOfferIds.clear();

        return result;
    } catch (error) {
        logBackground(`Export error: ${error.message}`, 'error');
        return {
            success: false,
            error: error.message
        };
    }
}

// Обработка одного запроса офферов
async function processOffersRequest(details) {
    if (isProcessing) return;

    try {
        isProcessing = true;

        // Собираем заголовки из оригинального запроса
        const headers = {};
        details.requestHeaders.forEach(header => {
            headers[header.name] = header.value;
        });

        // Выполняем запрос
        const response = await fetch(details.url, { headers });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        if (!data || !data.offers) return;

        // Фильтруем новые офферы
        const newOffers = data.offers.filter(offer => !processedOfferIds.has(offer.id));
        if (newOffers.length === 0) return;

        // Добавляем ID в сет обработанных
        newOffers.forEach(offer => processedOfferIds.add(offer.id));

        // Обрабатываем новые офферы
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

        // Добавляем в аккумулятор
        accumulatedOffers = [...accumulatedOffers, ...processedData];

        // Обновляем статистику в popup
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

// Перехват запросов
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

// Добавляем настройки планировщика
let schedulerSettings = {
    enabled: false,
    time: "08:00",
    days: [],
    lastRun: null,
    nextRun: null
};

// Загрузка настроек
async function loadSchedulerSettings() {
    try {
        const result = await chrome.storage.local.get('schedulerSettings');
        if (result.schedulerSettings) {
            schedulerSettings = result.schedulerSettings;
            updateNextRun();
        }
    } catch (error) {
        logBackground(`Error loading scheduler settings: ${error.message}`, 'error');
    }
}

// Сохранение настроек
async function saveSchedulerSettings(settings) {
    try {
        schedulerSettings = { ...schedulerSettings, ...settings };
        await chrome.storage.local.set({ schedulerSettings });
        updateNextRun();
        return { success: true };
    } catch (error) {
        logBackground(`Error saving scheduler settings: ${error.message}`, 'error');
        return { success: false, error: error.message };
    }
}

// Обновление времени следующего запуска
function updateNextRun() {
    if (!schedulerSettings.enabled || !schedulerSettings.time || !schedulerSettings.days.length) {
        schedulerSettings.nextRun = null;
        return;
    }

    const now = new Date();
    const [hours, minutes] = schedulerSettings.time.split(':').map(Number);

    // Находим следующий подходящий день
    let nextRun = new Date(now);
    nextRun.setHours(hours, minutes, 0, 0);

    if (nextRun <= now) {
        nextRun.setDate(nextRun.getDate() + 1);
    }

    while (!schedulerSettings.days.includes(nextRun.getDay())) {
        nextRun.setDate(nextRun.getDate() + 1);
    }

    schedulerSettings.nextRun = nextRun.toISOString();
}

// Проверка необходимости запуска
async function checkScheduledRun() {
    if (!schedulerSettings.enabled || !schedulerSettings.nextRun) return;

    const now = new Date();
    const nextRun = new Date(schedulerSettings.nextRun);

    if (now >= nextRun) {
        logBackground('Starting scheduled run');
        // Запускаем сбор данных
        await startScheduledRun();
        // Обновляем время следующего запуска
        schedulerSettings.lastRun = now.toISOString();
        updateNextRun();
        await saveSchedulerSettings({});
    }
}
// Запускаем проверку каждую минуту
setInterval(checkScheduledRun, 60000);

// Загружаем настройки при старте
loadSchedulerSettings();

// Выполнение запланированного запуска
async function startScheduledRun() {
    try {
        // Находим активную вкладку с Allegro
        const tabs = await chrome.tabs.query({
            url: [
                "*://allegro.pl/*",
                "*://salescenter.allegro.com/*"
            ]
        });

        if (tabs.length === 0) {
            logBackground('No Allegro tabs found for scheduled run', 'error');
            return;
        }

        // Отправляем команду на запуск пагинации
        await chrome.tabs.sendMessage(tabs[0].id, {
            action: "startPagination"
        });

        logBackground('Scheduled run started successfully');
    } catch (error) {
        logBackground(`Error in scheduled run: ${error.message}`, 'error');
    }
}



// Обработчик сообщений
// Обработчик сообщений в background.js
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "exportOffers") {
        // Выполняем экспорт и отправляем результат
        exportOffers().then(result => {
            sendResponse(result);
        });
        return true; // Указываем, что ответ будет асинхронным
    }

    if (message.action === "getStats") {
        sendResponse({
            accumulated: accumulatedOffers.length,
            uniqueIds: processedOfferIds.size
        });
        return true;
    }

    // Добавляем обработчики для планировщика
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