let isEnabled = true; // По умолчанию включено
let isAutoPaginationActive = false;
const OFFERS_URL_PATTERN = 'edge.salescenter.allegro.com/sale/offers';
const TARGET_URL = 'https://salescenter.allegro.com/my-assortment?limit=500&publication.status=ACTIVE&sellingMode.format=BUY_NOW&publication.marketplace=allegro-pl';

// Проверка и загрузка настроек при инициализации
chrome.storage.local.get(['isEnabled'], function (result) {
    // Если настройка отсутствует, устанавливаем по умолчанию включенное состояние
    isEnabled = result.isEnabled !== undefined ? result.isEnabled : true;
    sendLog(`Скрипт контента инициализирован с isEnabled: ${isEnabled}`, 'info');

    // Автоматический запуск
    handleUrlChange();
});

// Проверяем текущий URL и перенаправляем если нужно
if (window.location.href.includes('salescenter.allegro.com/my-sales')) {
    sendLog('Обнаружена страница my-sales, перенаправляем на целевой URL');
    window.location.href = TARGET_URL;
}

// Функция для проверки текущего URL
function isTargetPage() {
    return window.location.href.includes('salescenter.allegro.com/my-assortment') &&
        window.location.href.includes('publication.status=ACTIVE') &&
        window.location.href.includes('sellingMode.format=BUY_NOW');
}

// Проверяем текущий URL и выполняем соответствующие действия
async function handleUrlChange() {
    if (window.location.href.includes('salescenter.allegro.com/my-sales')) {
        sendLog('Обнаружена страница my-sales, перенаправляем на целевой URL');
        window.location.href = TARGET_URL;
    } else if (isTargetPage()) {
        sendLog('Обнаружена целевая страница, запускаем сбор данных');
        // Даем время на полную загрузку страницы
        await delay(2000);

        // Проверяем, не запущена ли уже пагинация
        if (!isAutoPaginationActive) {
            await startAutoPagination();
        }
    }
}

// Запускаем обработку URL при загрузке страницы и при изменении URL
handleUrlChange();

// Следим за изменениями URL
let lastUrl = location.href;
new MutationObserver(() => {
    if (location.href !== lastUrl) {
        lastUrl = location.href;
        handleUrlChange();
    }
}).observe(document, { subtree: true, childList: true });

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
                    data: response.data,
                    fileName: response.fileName
                }).catch(() => {
                    // Ошибка при отправке в popup не критична
                    sendLog('Не удалось отправить данные в popup, но данные были успешно собраны', 'info');
                });

                sendLog(`Финальный экспорт завершен: ${response.count} офферов`);
                resolve(true);
            } else {
                sendLog('Ошибка при финальном экспорте: ' + (response?.error || 'Неизвестная ошибка'), 'error');
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
    // Проверяем логин перед началом
    try {
        const loginCheck = await new Promise((resolve, reject) => {
            chrome.runtime.sendMessage({ action: "checkLogin" }, response => {
                if (chrome.runtime.lastError) {
                    reject(chrome.runtime.lastError);
                } else {
                    resolve(response);
                }
            });
        });

        if (loginCheck.status === 'redirecting') {
            sendLog('Перенаправление на страницу логина');
            return;
        }

        if (!isEnabled) {
            sendLog('Расширение отключено, пагинация не будет запущена');
            return;
        }

        if (isAutoPaginationActive) {
            sendLog('Пагинация уже активна, не запускаем повторно');
            return;
        }

        isAutoPaginationActive = true;
        let wasLastPage = false;
        sendLog('Запущена автоматическая пагинация');

        try {
            // Проверяем начальное состояние
            let buttonStatus = checkNextButton();
            if (buttonStatus === 'no-button' || buttonStatus === 'disabled') {
                wasLastPage = true;
                sendLog('Кнопка "следующая страница" не найдена или неактивна');
            } else {
                // Листаем страницы
                while (isEnabled && isAutoPaginationActive) {
                    await delay(5000); // Ждем 5 секунд между кликами

                    // Проверяем кнопку перед кликом
                    buttonStatus = checkNextButton();
                    if (buttonStatus !== 'active') {
                        wasLastPage = true;
                        sendLog('Достигнута последняя страница (кнопка не активна)');
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
    } catch (error) {
        sendLog(`Не удалось проверить статус логина: ${error.message}`, 'error');
        isAutoPaginationActive = false;
    }
}

// Расширяем существующий обработчик сообщений
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    sendLog(`Получено сообщение: ${JSON.stringify(message)}`, 'info');

    if (message.action === "ping") {
        sendResponse({ status: "pong" });
    }
    else if (message.action === "toggleExtension") {
        isEnabled = message.enabled;
        sendLog(`Расширение ${isEnabled ? 'включено' : 'выключено'}`, 'info');
        if (isEnabled && !isAutoPaginationActive && isTargetPage()) {
            // При включении расширения запускаем автопагинацию, если мы на целевой странице
            startAutoPagination();
        } else if (!isEnabled) {
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

    return true; // Удерживаем соединение открытым для асинхронного ответа
});

function sendLog(message, type = 'info') {
    console.log(`[Content][${type}]`, message);
    chrome.runtime.sendMessage({
        action: "log",
        message: typeof message === 'object' ? JSON.stringify(message) : message,
        type: type
    }).catch(() => { }); // Игнорируем ошибки отправки логов
}

sendLog('Скрипт контента загружен и инициализирован');

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
        sendLog(`Перехвачен fetch запрос: ${url}`, 'request');
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
                sendLog('Получен ответ на fetch запрос', 'response');
                processAndSaveOffers(data);
            }).catch(error => {
                sendLog(`Ошибка при разборе ответа: ${error.message}`, 'error');
            });

            return response;
        } catch (error) {
            sendLog(`Ошибка fetch: ${error.message}`, 'error');
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
        sendLog(`Перехвачен XHR ${method} запрос: ${url}`, 'request');
    }
    return originalXHROpen.apply(this, [method, url, ...args]);
};

XMLHttpRequest.prototype.send = function (data) {
    if (isEnabled && isOffersUrl(this._url)) {
        this.addEventListener('load', function () {
            try {
                const response = JSON.parse(this.responseText);
                sendLog('Получен ответ на XHR запрос', 'response');
                processAndSaveOffers(response);
            } catch (error) {
                sendLog(`Ошибка при обработке ответа XHR: ${error.message}`, 'error');
            }
        });
    }
    return originalXHRSend.apply(this, arguments);
};

// Функция обработки и сохранения офферов
function processAndSaveOffers(data) {
    if (!data || !data.offers) {
        sendLog('Получены неверные данные', 'error');
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
        sendLog(`Обработка ${processedOffers.length} офферов`, 'info');

        chrome.storage.local.set({
            [storageKey]: processedOffers
        }, () => {
            sendLog(`Сохранено ${processedOffers.length} офферов с ключом: ${storageKey}`, 'info');
            chrome.runtime.sendMessage({
                action: "offersUpdated",
                count: processedOffers.length
            });
        });
    } catch (error) {
        sendLog(`Ошибка при обработке офферов: ${error.message}`, 'error');
    }
}

// Функция для периодической проверки состояния страницы
async function periodicCheck() {
    try {
        // Если мы на целевой странице и пагинация не активна - запускаем ее
        if (isTargetPage() && !isAutoPaginationActive && isEnabled) {
            sendLog('Периодическая проверка: запуск пагинации на целевой странице');
            await startAutoPagination();
        }
    } catch (error) {
        sendLog(`Ошибка в периодической проверке: ${error.message}`, 'error');
    }
}

// Запускаем периодическую проверку каждую минуту
setInterval(periodicCheck, 60000);