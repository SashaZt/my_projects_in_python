// ==UserScript==
// @name         Capture and Save All Requests
// @namespace    http://tampermonkey.net/
// @version      0.7
// @description  Перехватывает и сохраняет все сетевые запросы в localStorage, экспортирует в JSON по команде stop_script, сохраняет состояние между перезагрузками
// @author       You
// @match        https://salescenter.allegro.com/*
// @grant        none
// ==/UserScript==

(function () {
    'use strict';

    let isCapturing = localStorage.getItem('captureState') === 'active'; // Проверяем состояние перехвата
    let originalFetch = window.fetch; // Сохраняем оригинальный fetch
    let originalXHROpen = XMLHttpRequest.prototype.open; // Сохраняем оригинальный open
    let originalXHRSend = XMLHttpRequest.prototype.send; // Сохраняем оригинальный send

    // Функция для парсинга query-параметров из URL
    function parseQueryParams(url) {
        try {
            const urlObj = new URL(url);
            const params = {};
            urlObj.searchParams.forEach((value, key) => {
                params[key] = value;
            });
            return params;
        } catch (e) {
            return {};
        }
    }

    // Функция для сохранения запросов в localStorage
    function saveRequest(requestData) {
        try {
            if (!isCapturing) return;
            let requests = JSON.parse(localStorage.getItem('networkRequests') || '[]');
            requests.push(requestData);
            localStorage.setItem('networkRequests', JSON.stringify(requests));
        } catch (e) {
            // Логирование отключено
        }
    }

    // Перехват XMLHttpRequest
    function setupXHRCapture() {
        XMLHttpRequest.prototype.open = function (method, url) {
            try {
                if (!isCapturing) return originalXHROpen.apply(this, arguments);
                this._requestData = {
                    method,
                    url,
                    type: 'xhr',
                    timestamp: new Date().toISOString(),
                    queryParams: parseQueryParams(url)
                };
            } catch (e) {
                // Логирование отключено
            }
            return originalXHROpen.apply(this, arguments);
        };

        XMLHttpRequest.prototype.send = function (body) {
            try {
                if (!isCapturing || !this._requestData) return originalXHRSend.apply(this, arguments);
                this._requestData.body = body ? body.toString() : null;
                this._requestData.headers = {};
                requestData.cookies = document.cookie; // Добавил
                saveRequest(this._requestData);
            } catch (e) {
                // Логирование отключено
            }
            return originalXHRSend.apply(this, arguments);
        };
    }

    // Перехват fetch
    function setupFetchCapture() {
        window.fetch = function (input, init = {}) {
            try {
                if (!isCapturing) return originalFetch.apply(this, arguments);
                const requestData = {
                    method: init.method || 'GET',
                    url: typeof input === 'string' ? input : input.url,
                    type: 'fetch',
                    headers: init.headers ? Object.fromEntries(new Headers(init.headers)) : {},
                    timestamp: new Date().toISOString(),
                    queryParams: parseQueryParams(typeof input === 'string' ? input : input.url)
                };
                if (init && init.body instanceof FormData) {
                    requestData.body = Object.fromEntries(init.body.entries());
                } else {
                    requestData.body = init && init.body ? init.body.toString() : null;
                }
                requestData.cookies = document.cookie; // Добавил
                saveRequest(requestData);
            } catch (e) {
                // Логирование отключено
            }
            return originalFetch.apply(this, arguments);
        };
    }

    // Перехват прямой отправки форм
    function setupFormCapture() {
        document.addEventListener('submit', function (event) {
            try {
                if (!isCapturing) return;
                const form = event.target;
                const formData = new FormData(form);
                const requestData = {
                    method: form.method.toUpperCase(),
                    url: form.action,
                    type: 'form',
                    body: Object.fromEntries(formData.entries()),
                    headers: { 'Content-Type': form.enctype || 'application/x-www-form-urlencoded' },
                    timestamp: new Date().toISOString(),
                    queryParams: parseQueryParams(form.action)
                };
                requestData.cookies = document.cookie; // Добавил
                saveRequest(requestData);
            } catch (e) {
                // Логирование отключено
            }
        });
    }

    // Функция для экспорта запросов в JSON-файл
    window.exportSavedRequests = function () {
        try {
            const requests = JSON.parse(localStorage.getItem('networkRequests') || '[]');
            const blob = new Blob([JSON.stringify(requests, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `network_requests_${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
            a.click();
            URL.revokeObjectURL(url);
        } catch (e) {
            // Логирование отключено
        }
    };

    // Функция для просмотра сохраненных запросов
    window.viewSavedRequests = function () {
        try {
            return JSON.parse(localStorage.getItem('networkRequests') || '[]');
        } catch (e) {
            // Логирование отключено
            return [];
        }
    };

    // Функция для очистки сохраненных запросов
    window.clearSavedRequests = function () {
        try {
            localStorage.removeItem('networkRequests');
        } catch (e) {
            // Логирование отключено
        }
    };

    // Функция для запуска перехвата
    window.start_script = function () {
        try {
            if (isCapturing) return;
            isCapturing = true;
            localStorage.setItem('captureState', 'active');
            setupXHRCapture();
            setupFetchCapture();
            setupFormCapture();
        } catch (e) {
            // Логирование отключено
        }
    };

    // Функция для остановки перехвата и экспорта
    window.stop_script = function () {
        try {
            if (!isCapturing) return;
            isCapturing = false;
            localStorage.removeItem('captureState');
            XMLHttpRequest.prototype.open = originalXHROpen;
            XMLHttpRequest.prototype.send = originalXHRSend;
            window.fetch = originalFetch;
            window.exportSavedRequests();
            window.clearSavedRequests();
        } catch (e) {
            // Логирование отключено
        }
    };

    // Возобновляем перехват, если он был активен
    if (isCapturing) {
        window.start_script();
    }
})();