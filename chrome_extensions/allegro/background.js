// Глобальные переменные
let isAutoLoginEnabled = true;
let accumulatedOffers = [];
const processedOfferIds = new Set();
let isProcessing = false;

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
    if (type !== 'debug') {
        chrome.runtime.sendMessage({
            action: "log",
            message: `[Background] ${message}`,
            type: type
        }).catch(() => { });
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

// Функция экспорта офферов
async function exportOffers() {
    if (accumulatedOffers.length === 0) {
        return {
            success: false,
            message: "No offers to export"
        };
    }

    try {
        const result = {
            success: true,
            count: accumulatedOffers.length,
            data: accumulatedOffers
        };

        logBackground(`Prepared ${accumulatedOffers.length} offers for export`);
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

// Функции планировщика
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

function updateNextRun() {
    if (!schedulerSettings.enabled || !schedulerSettings.time || !schedulerSettings.days.length) {
        schedulerSettings.nextRun = null;
        return;
    }

    const now = new Date();
    const [hours, minutes] = schedulerSettings.time.split(':').map(Number);
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

async function startScheduledRun() {
    try {
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

        await chrome.tabs.sendMessage(tabs[0].id, {
            action: "startPagination"
        });

        logBackground('Scheduled run started successfully');
    } catch (error) {
        logBackground(`Error in scheduled run: ${error.message}`, 'error');
    }
}

async function checkScheduledRun() {
    if (!schedulerSettings.enabled || !schedulerSettings.nextRun) return;

    const now = new Date();
    const nextRun = new Date(schedulerSettings.nextRun);

    if (now >= nextRun) {
        logBackground('Starting scheduled run');
        await startScheduledRun();
        schedulerSettings.lastRun = now.toISOString();
        updateNextRun();
        await saveSchedulerSettings({});
    }
}

// Инициализация и слушатели событий
loadSchedulerSettings();
setInterval(checkScheduledRun, 60000);

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

// Основной обработчик сообщений
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
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