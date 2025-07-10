// ==UserScript==
// @name         Allegro Auto Login & Cookie Sender
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Автоматический логин в Allegro и отправка куки через POST запрос
// @author       You
// @match        https://allegro.com/log-in*
// @match        https://allegro.pl/log-in*
// @match        https://salescenter.allegro.com/*
// @grant        GM_xmlhttpRequest
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_log
// ==/UserScript==

(function () {
    'use strict';

    // КОНФИГУРАЦИЯ - НАСТРОЙТЕ ПОД СЕБЯ
    const CONFIG = {
        // URL для отправки куки (замените на свой)
        WEBHOOK_URL: 'https://your-server.com/api/cookies',

        // Учетные данные для логина
        USERNAME: 'wowlet',
        PASSWORD: 'i8##-aUJ5Dviz&8',

        // Включить дебаг логи
        DEBUG: true
    };

    // Функция логирования
    function log(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const logMessage = `[${timestamp}][${type.toUpperCase()}] ${message}`;

        if (CONFIG.DEBUG) {
            console.log(logMessage);
        }
        GM_log(logMessage);
    }

    // Функция задержки
    function delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Функция получения всех куки
    function getAllCookies() {
        const cookies = {};
        document.cookie.split(';').forEach(cookie => {
            const [name, value] = cookie.trim().split('=');
            if (name && value) {
                cookies[name] = decodeURIComponent(value);
            }
        });
        return cookies;
    }

    // Функция отправки куки на сервер
    function sendCookiesToServer(cookies) {
        const payload = {
            timestamp: new Date().toISOString(),
            url: window.location.href,
            userAgent: navigator.userAgent,
            cookies: cookies,
            sessionId: cookies.QXLSESSID || 'unknown'
        };

        log('Отправляем куки на сервер...');

        GM_xmlhttpRequest({
            method: 'POST',
            url: CONFIG.WEBHOOK_URL,
            headers: {
                'Content-Type': 'application/json',
                'User-Agent': navigator.userAgent
            },
            data: JSON.stringify(payload),
            onload: function (response) {
                if (response.status >= 200 && response.status < 300) {
                    log('Куки успешно отправлены на сервер', 'success');
                } else {
                    log(`Ошибка при отправке куки: ${response.status} - ${response.statusText}`, 'error');
                }
            },
            onerror: function (error) {
                log(`Ошибка сети при отправке куки: ${error}`, 'error');
            },
            ontimeout: function () {
                log('Таймаут при отправке куки', 'error');
            },
            timeout: 10000
        });
    }

    // Функция ожидания элемента
    async function waitForElement(selector, timeout = 10000) {
        return new Promise((resolve, reject) => {
            const startTime = Date.now();

            const checkElement = () => {
                const element = document.querySelector(selector);
                if (element) {
                    resolve(element);
                    return;
                }

                if (Date.now() - startTime >= timeout) {
                    reject(new Error(`Элемент ${selector} не найден после ${timeout}мс`));
                    return;
                }

                requestAnimationFrame(checkElement);
            };

            checkElement();
        });
    }

    // Функция симуляции пользовательского ввода
    function simulateInput(element, value) {
        element.focus();
        element.value = value;

        // Генерируем события
        const events = ['input', 'change', 'blur'];
        events.forEach(eventName => {
            element.dispatchEvent(new Event(eventName, { bubbles: true }));
        });
    }

    // Основная функция автологина
    // async function performAutoLogin() {
    //     try {
    //         log('Начинаем процесс автологина...');

    //         // Ждем загрузки формы
    //         const loginInput = await waitForElement('input[name="login"]');
    //         const passwordInput = await waitForElement('input[type="password"]');
    //         const submitButton = await waitForElement('button[type="submit"]');

    //         log('Форма логина найдена, заполняем данные...');

    //         // Заполняем форму
    //         await delay(500);
    //         simulateInput(loginInput, CONFIG.USERNAME);

    //         await delay(500);
    //         simulateInput(passwordInput, CONFIG.PASSWORD);

    //         await delay(500);

    //         log('Отправляем форму...');
    //         submitButton.click();

    //         // Ждем редиректа или ошибки
    //         await waitForLoginResult();

    //     } catch (error) {
    //         log(`Ошибка при автологине: ${error.message}`, 'error');
    //     }
    // }

    // Функция ожидания результата логина
    // async function waitForLoginResult(timeout = 15000) {
    //     const startTime = Date.now();
    //     const startUrl = window.location.href;

    //     return new Promise((resolve) => {
    //         const checkResult = () => {
    //             // Проверяем редирект
    //             if (window.location.href !== startUrl) {
    //                 log('Успешный редирект после логина');
    //                 resolve(true);
    //                 return;
    //             }

    //             // Проверяем ошибку
    //             const errorElement = document.querySelector('[data-testid="login-error"]');
    //             if (errorElement) {
    //                 log(`Ошибка логина: ${errorElement.textContent}`, 'error');
    //                 resolve(false);
    //                 return;
    //             }

    //             // Проверяем таймаут
    //             if (Date.now() - startTime >= timeout) {
    //                 log('Таймаут ожидания результата логина', 'warn');
    //                 resolve(false);
    //                 return;
    //             }

    //             setTimeout(checkResult, 500);
    //         };

    //         checkResult();
    //     });
    // }

    // Функция мониторинга куки
    function startCookieMonitoring() {
        let lastSessionId = '';

        function checkCookies() {
            const cookies = getAllCookies();
            const currentSessionId = cookies.QXLSESSID || '';

            // Если появился новый session ID, отправляем куки
            if (currentSessionId && currentSessionId !== lastSessionId) {
                log(`Обнаружена новая сессия: ${currentSessionId.substring(0, 10)}...`);
                lastSessionId = currentSessionId;

                // Ждем немного для установки всех куки, затем отправляем
                setTimeout(() => {
                    const allCookies = getAllCookies();
                    sendCookiesToServer(allCookies);
                }, 3000);
            }
        }

        // Проверяем куки каждые 5 секунд
        setInterval(checkCookies, 5000);

        // Также проверяем при первой загрузке
        setTimeout(checkCookies, 2000);
    }

    // Основная логика
    function initialize() {
        log('Скрипт Tampermonkey инициализирован');

        // Если мы на странице логина
        if (window.location.href.includes('/log-in')) {
            log('Обнаружена страница логина');

            // Проверяем, есть ли уже активная сессия
            const cookies = getAllCookies();
            if (cookies.QXLSESSID) {
                log('Уже есть активная сессия, пропускаем автологин');
                return;
            }

            // Ждем полной загрузки страницы, затем логинимся
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => {
                    setTimeout(performAutoLogin, 2000);
                });
            } else {
                setTimeout(performAutoLogin, 2000);
            }
        }

        // Запускаем мониторинг куки на всех страницах Allegro
        if (window.location.href.includes('allegro.')) {
            startCookieMonitoring();
        }
    }

    // Функция для ручного запуска (можно вызвать из консоли)
    window.allegroAutoLogin = performAutoLogin;
    window.allegroSendCookies = () => {
        const cookies = getAllCookies();
        sendCookiesToServer(cookies);
    };

    // Запускаем инициализацию
    initialize();

    // Дополнительная проверка для случаев динамической загрузки
    let urlCheck = window.location.href;
    setInterval(() => {
        if (window.location.href !== urlCheck) {
            urlCheck = window.location.href;
            log(`URL изменился на: ${urlCheck}`);

            if (urlCheck.includes('/log-in')) {
                setTimeout(performAutoLogin, 1000);
            }
        }
    }, 1000);

})();