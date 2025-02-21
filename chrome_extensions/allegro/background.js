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

// Обработка одного запроса офферов
async function processOffersRequest(details) {
    if (isProcessing) {
        return;
    }

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

        if (!data || !data.offers) {
            return;
        }

        // Фильтруем новые офферы
        const newOffers = data.offers.filter(offer => !processedOfferIds.has(offer.id));

        if (newOffers.length > 0) {
            // Добавляем ID в сет обработанных
            newOffers.forEach(offer => processedOfferIds.add(offer.id));

            // Обрабатываем новые офферы, оставляя только нужные поля
            const processedData = newOffers.map(offer => ({
                id: offer.id,
                name: offer.name,
                stats: offer.stats
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
        }

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

// Обработчик сообщений
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "exportOffers") {
        if (accumulatedOffers.length > 0) {
            try {
                // Создаём файл только с массивом офферов
                sendResponse({
                    success: true,
                    data: accumulatedOffers,
                    count: accumulatedOffers.length
                });

                logBackground(`Exported ${accumulatedOffers.length} offers`);

                // Очищаем аккумулятор после экспорта
                accumulatedOffers = [];
                processedOfferIds.clear();
            } catch (error) {
                logBackground(`Export error: ${error.message}`, 'error');
                sendResponse({
                    success: false,
                    error: error.message
                });
            }
        } else {
            sendResponse({
                success: false,
                message: "No offers to export"
            });
        }
        return true;
    }

    if (message.action === "getStats") {
        sendResponse({
            accumulated: accumulatedOffers.length,
            uniqueIds: processedOfferIds.size
        });
        return true;
    }

    sendResponse({ status: "ok" });
    return false;
});