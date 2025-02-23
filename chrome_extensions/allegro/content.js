let isEnabled = true;
let isAutoPaginationActive = false;
const OFFERS_URL_PATTERN = 'edge.salescenter.allegro.com/sale/offers';

// Функция для задержки
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Функция для проверки наличия кнопки следующей страницы
function hasNextPageButton() {
    const nextButton = document.querySelector('button[aria-label="następna strona"]');
    return nextButton && !nextButton.disabled;
}

// Функция для клика по кнопке следующей страницы
async function clickNextPage() {
    const nextButton = document.querySelector('button[aria-label="następna strona"]');
    if (nextButton && !nextButton.disabled) {
        nextButton.click();
        sendLog('Переход на следующую страницу');
        return true;
    }
    return false;
}
// Функция экспорта данных
async function exportCollectedData() {
    sendLog('Начинаем финальный экспорт данных');
    // Ждем дополнительно 2 секунды для завершения всех запросов
    await delay(2000);

    return new Promise((resolve, reject) => {
        chrome.runtime.sendMessage({
            action: "exportOffers"
        }, function (response) {
            if (response && response.success) {
                // После успешного получения данных, отправляем их в popup для скачивания
                chrome.runtime.sendMessage({
                    action: "downloadData",
                    data: response.data
                }).catch(() => {
                    // Ошибка при отправке в popup не критична
                    sendLog('Не удалось отправить данные в popup, но данные были успешно собраны', 'info');
                });

                sendLog(`Финальный экспорт завершен: ${response.count} офферов`);
                resolve(true);
            } else {
                sendLog('Ошибка при финальном экспорте', 'error');
                reject(new Error(response?.error || 'Export failed'));
            }
        });
    });
}
// Функция проверки наличия кнопки и её состояния
function checkNextButton() {
    const nextButton = document.querySelector('button[aria-label="następna strona"]');
    if (!nextButton) return 'no-button';
    if (nextButton.disabled) return 'disabled';
    return 'active';
}

// Функция для ожидания загрузки контента
async function waitForContentUpdate() {
    await delay(1000); // Минимальная задержка

    // Ждем еще немного если контент обновляется
    for (let i = 0; i < 10; i++) {
        const status = checkNextButton();
        if (status !== 'active') break;
        await delay(500);
    }
}

// Функция автоматической пагинации
async function startAutoPagination() {
    if (!isEnabled || isAutoPaginationActive) return;

    isAutoPaginationActive = true;
    let wasLastPage = false;
    sendLog('Запущена автоматическая пагинация');

    try {
        // Проверяем начальное состояние
        let buttonStatus = checkNextButton();
        if (buttonStatus === 'no-button' || buttonStatus === 'disabled') {
            wasLastPage = true;
        } else {
            // Листаем страницы
            while (isEnabled && isAutoPaginationActive) {
                await delay(5000); // Ждем 5 секунд между кликами

                // Проверяем кнопку перед кликом
                buttonStatus = checkNextButton();
                if (buttonStatus !== 'active') {
                    wasLastPage = true;
                    break;
                }

                // Кликаем и ждем обновления
                const nextButton = document.querySelector('button[aria-label="następna strona"]');
                nextButton.click();
                sendLog('Переход на следующую страницу');

                // Ждем обновления контента
                await waitForContentUpdate();
            }
        }

        sendLog('Автоматическая пагинация завершена');

        // Если это была последняя страница, запускаем экспорт
        if (wasLastPage) {
            sendLog('Достигнута последняя страница, начинаем экспорт');
            await delay(2000); // Ждем завершения последних запросов
            await exportCollectedData();
        }
    } catch (error) {
        sendLog(`Ошибка при автоматической пагинации: ${error.message}`, 'error');
    } finally {
        isAutoPaginationActive = false;
    }
}

// Расширяем существующий обработчик сообщений
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    sendLog(`Received message: ${JSON.stringify(message)}`, 'info');

    if (message.action === "ping") {
        sendResponse({ status: "pong" });
    }
    else if (message.action === "toggleExtension") {
        isEnabled = message.enabled;
        sendLog(`Extension ${isEnabled ? 'enabled' : 'disabled'}`, 'info');
        if (isEnabled) {
            // При включении расширения запускаем автопагинацию
            startAutoPagination();
        } else {
            // При выключении останавливаем
            isAutoPaginationActive = false;
        }
        sendResponse({ status: "ok" });
    }
    else if (message.action === "startPagination") {
        startAutoPagination();
        sendResponse({ status: "ok" });
    }
    else if (message.action === "stopPagination") {
        isAutoPaginationActive = false;
        sendResponse({ status: "ok" });
    }

    return false;
});

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