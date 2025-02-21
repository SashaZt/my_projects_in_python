let isEnabled = true;
const OFFERS_URL_PATTERN = 'edge.salescenter.allegro.com/sale/offers';

function sendLog(message, type = 'info') {
    console.log(`[Content][${type}]`, message);
    chrome.runtime.sendMessage({
        action: "log",
        message: typeof message === 'object' ? JSON.stringify(message) : message,
        type: type
    }).catch(() => { });
}

sendLog('Content script loaded and initialized');

// Функция для проверки URL
function isOffersUrl(url) {
    return url.includes(OFFERS_URL_PATTERN);
}

// Создаем перехватчик fetch
const originalFetch = window.fetch;
window.fetch = async function (...args) {
    const [resource, config] = args;
    const url = (typeof resource === 'string') ? resource : resource.url;

    if (isEnabled && isOffersUrl(url)) {
        sendLog(`Intercepted fetch request to: ${url}`, 'request');
        try {
            // Клонируем и модифицируем конфигурацию
            const newConfig = {
                ...config,
                headers: {
                    ...(config?.headers || {}),
                    'accept': 'application/vnd.allegro.web.v2+json',
                    'accept-language': 'pl-PL',
                }
            };

            // Выполняем запрос
            const response = await originalFetch(url, newConfig);
            const clonedResponse = response.clone();

            // Обрабатываем ответ
            clonedResponse.json().then(data => {
                sendLog('Received fetch response', 'response');
                processAndSaveOffers(data);
            }).catch(error => {
                sendLog(`Error parsing fetch response: ${error.message}`, 'error');
            });

            return response;
        } catch (error) {
            sendLog(`Fetch error: ${error.message}`, 'error');
            return originalFetch(...args);
        }
    }
    return originalFetch(...args);
};

// Создаем перехватчик XMLHttpRequest
const originalXHROpen = XMLHttpRequest.prototype.open;
const originalXHRSend = XMLHttpRequest.prototype.send;

XMLHttpRequest.prototype.open = function (method, url, ...args) {
    this._url = url;
    this._method = method;
    if (isEnabled && isOffersUrl(url)) {
        sendLog(`Intercepted XHR ${method} request to: ${url}`, 'request');
    }
    return originalXHROpen.apply(this, [method, url, ...args]);
};

XMLHttpRequest.prototype.send = function (data) {
    if (isEnabled && isOffersUrl(this._url)) {
        this.addEventListener('load', function () {
            try {
                const response = JSON.parse(this.responseText);
                sendLog('Received XHR response', 'response');
                processAndSaveOffers(response);
            } catch (error) {
                sendLog(`Error processing XHR response: ${error.message}`, 'error');
            }
        });
    }
    return originalXHRSend.apply(this, arguments);
};

// Функция обработки и сохранения офферов
function processAndSaveOffers(data) {
    if (!data || !data.offers) {
        sendLog('Invalid data structure received', 'error');
        return;
    }

    try {
        const processedOffers = data.offers.map(offer => ({
            id: offer.id,
            name: offer.name,
            price: offer.price || {},
            stats: offer.stats || {},
            parameters: offer.parameters || [],
            stock: offer.stock || {},
            category: offer.category || {},
            publication: offer.publication || {},
            sellingMode: offer.sellingMode || {},
            timestamp: new Date().toISOString()
        }));

        const storageKey = `offers_${new Date().getTime()}`;
        sendLog(`Processing ${processedOffers.length} offers`, 'info');

        chrome.storage.local.set({
            [storageKey]: processedOffers
        }, () => {
            sendLog(`Saved ${processedOffers.length} offers with key: ${storageKey}`, 'info');
            chrome.runtime.sendMessage({
                action: "offersUpdated",
                count: processedOffers.length
            });
        });
    } catch (error) {
        sendLog(`Error processing offers: ${error.message}`, 'error');
    }
}

// Обработчик сообщений
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    sendLog(`Received message: ${JSON.stringify(message)}`, 'info');

    if (message.action === "ping") {
        sendResponse({ status: "pong" });
    }
    else if (message.action === "toggleExtension") {
        isEnabled = message.enabled;
        sendLog(`Extension ${isEnabled ? 'enabled' : 'disabled'}`, 'info');
        sendResponse({ status: "ok" });
    }

    return false;
});

// Инициализация состояния
chrome.storage.local.get(['isEnabled'], function (result) {
    isEnabled = result.isEnabled !== false;
    sendLog(`Initial state: ${isEnabled ? 'enabled' : 'disabled'}`, 'info');
});