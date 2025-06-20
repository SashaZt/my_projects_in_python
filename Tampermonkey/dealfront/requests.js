// ==UserScript==
// @name         Dealfront API Response Interceptor
// @namespace    http://tampermonkey.net/
// @version      1.1
// @description  Intercept POST requests to search-contacts API and save responses as JSON
// @author       You
// @match        https://app.dealfront.com/*
// @grant        none
// ==/UserScript==

(function () {
    'use strict';

    // Массив для хранения всех перехваченных ответов
    let interceptedResponses = [];

    // Функция для сохранения JSON файла
    function downloadJSON(data, filename) {
        const blob = new Blob([JSON.stringify(data, null, 2)], {
            type: 'application/json'
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // Функция для создания кнопки скачивания
    function createDownloadButton() {
        const button = document.createElement('button');
        button.innerHTML = `📥 Скачать данные (${interceptedResponses.length})`;
        button.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            z-index: 10000;
            padding: 10px 15px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        `;

        button.addEventListener('click', () => {
            if (interceptedResponses.length === 0) {
                alert('Нет данных для скачивания');
                return;
            }

            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const filename = `dealfront-contacts-${timestamp}.json`;
            downloadJSON(interceptedResponses, filename);
        });

        return button;
    }

    // Перехват XMLHttpRequest
    const originalXHR = window.XMLHttpRequest;
    window.XMLHttpRequest = function () {
        const xhr = new originalXHR();
        const originalOpen = xhr.open;
        const originalSend = xhr.send;

        let method, url;

        xhr.open = function (m, u) {
            method = m;
            url = u;
            return originalOpen.apply(this, arguments);
        };

        xhr.send = function () {
            if (method === 'POST' && url.includes('backend/search-contacts')) {
                console.log('🔍 Перехвачен POST запрос:', url);

                const originalOnReadyStateChange = xhr.onreadystatechange;
                xhr.onreadystatechange = function () {
                    if (xhr.readyState === 4 && xhr.status === 200) {
                        try {
                            const responseData = JSON.parse(xhr.responseText);
                            const interceptData = {
                                timestamp: new Date().toISOString(),
                                url: url,
                                status: xhr.status,
                                response: responseData
                            };

                            interceptedResponses.push(interceptData);
                            console.log('✅ Данные сохранены:', interceptData);

                            // Обновляем счетчик на кнопке
                            updateButtonCounter();

                        } catch (e) {
                            console.error('❌ Ошибка парсинга JSON:', e);
                        }
                    }

                    if (originalOnReadyStateChange) {
                        return originalOnReadyStateChange.apply(this, arguments);
                    }
                };
            }

            return originalSend.apply(this, arguments);
        };

        return xhr;
    };

    // Перехват fetch API
    const originalFetch = window.fetch;
    window.fetch = function (resource, options = {}) {
        const url = typeof resource === 'string' ? resource : resource.url;
        const method = options.method || 'GET';

        if (method === 'POST' && url.includes('backend/search-contacts')) {
            console.log('🔍 Перехвачен fetch POST запрос:', url);

            return originalFetch.apply(this, arguments).then(response => {
                if (response.ok) {
                    const clonedResponse = response.clone();
                    clonedResponse.json().then(data => {
                        const interceptData = {
                            timestamp: new Date().toISOString(),
                            url: url,
                            status: response.status,
                            response: data
                        };

                        interceptedResponses.push(interceptData);
                        console.log('✅ Данные сохранены (fetch):', interceptData);

                        // Обновляем счетчик на кнопке
                        updateButtonCounter();

                    }).catch(e => {
                        console.error('❌ Ошибка парсинга JSON (fetch):', e);
                    });
                }
                return response;
            });
        }

        return originalFetch.apply(this, arguments);
    };

    // Создание и добавление кнопки на страницу
    let downloadButton;

    function updateButtonCounter() {
        if (downloadButton) {
            downloadButton.innerHTML = `📥 Скачать данные (${interceptedResponses.length})`;
        }
    }

    function initButton() {
        downloadButton = createDownloadButton();
        document.body.appendChild(downloadButton);
    }

    // Ждем загрузки DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initButton);
    } else {
        initButton();
    }

    // Добавляем кнопку очистки данных
    function createClearButton() {
        const button = document.createElement('button');
        button.innerHTML = '🗑️ Очистить';
        button.style.cssText = `
            position: fixed;
            top: 60px;
            right: 10px;
            z-index: 10000;
            padding: 8px 12px;
            background: #f44336;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 12px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        `;

        button.addEventListener('click', () => {
            if (confirm('Очистить все сохраненные данные?')) {
                interceptedResponses = [];
                updateButtonCounter();
                console.log('🗑️ Данные очищены');
            }
        });

        return button;
    }

    // Переменные для автоматической пагинации
    let isAutoRunning = false;
    let autoInterval;

    // Функция для поиска кнопок пагинации
    function findPaginationButtons() {
        // Ищем по XPath
        const xpath = "//a[@class='eb-pagination-button']";
        const result = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);

        const buttons = [];
        for (let i = 0; i < result.snapshotLength; i++) {
            buttons.push(result.snapshotItem(i));
        }

        return buttons;
    }

    // Функция для клика по последней кнопке пагинации
    function clickLastPaginationButton() {
        const buttons = findPaginationButtons();
        console.log('🔍 Найдено кнопок пагинации:', buttons.length);

        if (buttons.length > 0) {
            const lastButton = buttons[buttons.length - 1];
            console.log('➡️ Кликаем по последней кнопке:', lastButton.textContent);

            // Проверяем, не отключена ли кнопка
            if (lastButton.classList.contains('disabled') || lastButton.getAttribute('disabled')) {
                console.log('⏹️ Кнопка отключена, останавливаем автоматизацию');
                stopAutoRun();
                return false;
            }

            lastButton.click();
            return true;
        } else {
            console.log('❌ Кнопки пагинации не найдены');
            return false;
        }
    }

    // Функция для запуска автоматической пагинации
    function startAutoRun() {
        if (isAutoRunning) return;

        isAutoRunning = true;
        console.log('🚀 Запуск автоматической пагинации');

        autoInterval = setInterval(() => {
            console.log('⏰ Попытка клика по кнопке пагинации...');
            const success = clickLastPaginationButton();

            if (!success) {
                console.log('⏹️ Автоматическая пагинация остановлена');
                stopAutoRun();
            }
        }, 5000); // 5 секунд пауза

        updateStartButton();
    }

    // Функция для остановки автоматической пагинации
    function stopAutoRun() {
        if (!isAutoRunning) return;

        isAutoRunning = false;
        if (autoInterval) {
            clearInterval(autoInterval);
            autoInterval = null;
        }
        console.log('⏹️ Автоматическая пагинация остановлена');
        updateStartButton();
    }

    // Функция для создания кнопки Старт/Стоп
    function createStartButton() {
        const button = document.createElement('button');
        button.innerHTML = '▶️ Старт';
        button.style.cssText = `
            position: fixed;
            top: 110px;
            right: 10px;
            z-index: 10000;
            padding: 10px 15px;
            background: #2196F3;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        `;

        button.addEventListener('click', () => {
            if (isAutoRunning) {
                stopAutoRun();
            } else {
                startAutoRun();
            }
        });

        return button;
    }

    // Функция для обновления текста кнопки старт/стоп
    function updateStartButton() {
        if (startButton) {
            if (isAutoRunning) {
                startButton.innerHTML = '⏹️ Стоп';
                startButton.style.background = '#f44336';
            } else {
                startButton.innerHTML = '▶️ Старт';
                startButton.style.background = '#2196F3';
            }
        }
    }

    // Создание кнопки тестирования поиска
    function createTestButton() {
        const button = document.createElement('button');
        button.innerHTML = '🔍 Тест';
        button.style.cssText = `
            position: fixed;
            top: 160px;
            right: 10px;
            z-index: 10000;
            padding: 8px 12px;
            background: #FF9800;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 12px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        `;

        button.addEventListener('click', () => {
            const buttons = findPaginationButtons();
            console.log('🔍 Найдено кнопок пагинации:', buttons.length);

            if (buttons.length > 0) {
                console.log('📋 Кнопки пагинации:');
                buttons.forEach((btn, index) => {
                    console.log(`${index + 1}. "${btn.textContent.trim()}" - ${btn.classList.contains('disabled') ? 'отключена' : 'активна'}`);
                });

                const lastButton = buttons[buttons.length - 1];
                console.log(`➡️ Последняя кнопка: "${lastButton.textContent.trim()}"`);
            } else {
                console.log('❌ Кнопки пагинации не найдены');
            }
        });

        return button;
    }

    // Глобальные переменные для кнопок
    let startButton;

    // Добавляем все кнопки
    setTimeout(() => {
        const clearButton = createClearButton();
        document.body.appendChild(clearButton);

        startButton = createStartButton();
        document.body.appendChild(startButton);

        const testButton = createTestButton();
        document.body.appendChild(testButton);
    }, 1000);

    console.log('🚀 Dealfront API Interceptor с автоматической пагинацией активирован');
})();