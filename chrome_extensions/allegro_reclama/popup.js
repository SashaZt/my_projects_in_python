document.addEventListener('DOMContentLoaded', function () {
    // Элементы интерфейса
    const loginButton = document.getElementById('loginButton');
    const loginStatusElement = document.getElementById('loginStatus');
    const logsElement = document.getElementById('logs');
    const clearLogsButton = document.getElementById('clearLogs');
    const toggleAutoScrollButton = document.getElementById('toggleAutoScroll');
    const loadConfigButton = document.getElementById('loadConfigButton');
    const configFileInput = document.getElementById('configFileInput');

    // Переменные
    let autoScroll = true;
    let logs = [];
    const MAX_LOGS = 1000;

    // Инициализация - проверка статуса логина
    checkLoginStatus();

    // Функция проверки статуса логина
    function checkLoginStatus() {
        chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
            if (tabs[0]) {
                chrome.runtime.sendMessage({
                    action: "checkLogin"
                }, function (response) {
                    if (response) {
                        updateLoginStatus(response.status);
                    } else {
                        updateLoginStatus('unknown');
                    }
                });
            }
        });
    }

    // Обновление статуса логина в UI
    function updateLoginStatus(status) {
        switch (status) {
            case 'logged_in':
                loginStatusElement.textContent = 'Авторизован';
                loginStatusElement.style.color = '#4CAF50';
                break;
            case 'not_logged_in':
                loginStatusElement.textContent = 'Не авторизован';
                loginStatusElement.style.color = '#f44336';
                break;
            case 'redirecting':
                loginStatusElement.textContent = 'Перенаправление...';
                loginStatusElement.style.color = '#2196F3';
                break;
            default:
                loginStatusElement.textContent = 'Неизвестно';
                loginStatusElement.style.color = '#757575';
        }
    }

    // Обработчик кнопки входа
    loginButton.addEventListener('click', function () {
        addLog('Начинаем процесс авторизации...', 'info');

        chrome.tabs.create({
            url: 'https://allegro.com/log-in?origin_url=https%3A%2F%2Fsalescenter.allegro.com'
        }, function (tab) {
            addLog('Открыта страница авторизации', 'info');
        });
    });

    // Обработчик загрузки конфигурации
    loadConfigButton.addEventListener('click', function () {
        configFileInput.click();
    });

    configFileInput.addEventListener('change', function (event) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function (e) {
                try {
                    const config = JSON.parse(e.target.result);
                    chrome.storage.local.set({ 'config_data': config }, function () {
                        addLog('Конфигурация успешно загружена и сохранена', 'info');
                    });
                } catch (error) {
                    addLog(`Ошибка при парсинге файла конфигурации: ${error.message}`, 'error');
                }
            };
            reader.readAsText(file);
        }
    });

    // Добавляем кнопку сохранения куки
    const saveCookiesButton = document.getElementById('saveCookiesButton');

    if (saveCookiesButton) {
        saveCookiesButton.addEventListener('click', function () {
            addLog('Запрос на сохранение куки...', 'info');

            chrome.runtime.sendMessage({
                action: "saveCookies"
            }, function (response) {
                if (response && response.success) {
                    addLog(`Куки успешно сохранены в файл: ${response.fileName}`, 'info');
                } else {
                    addLog('Не удалось сохранить куки: ' + (response?.error || 'неизвестная ошибка'), 'error');
                }
            });
        });
    }

    // Функция добавления логов
    function addLog(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = {
            timestamp,
            message: typeof message === 'object' ? JSON.stringify(message, null, 2) : message,
            type
        };

        logs.push(logEntry);
        if (logs.length > MAX_LOGS) {
            logs.shift();
        }

        const logElement = document.createElement('div');
        logElement.className = `log-entry log-${type}`;
        logElement.textContent = `[${timestamp}] ${logEntry.message}`;
        logsElement.appendChild(logElement);

        if (autoScroll) {
            logsElement.scrollTop = logsElement.scrollHeight;
        }

        chrome.storage.local.set({ 'extension_logs': logs });
    }

    // Загрузка логов при открытии
    chrome.storage.local.get(['extension_logs'], function (result) {
        if (result.extension_logs) {
            logs = result.extension_logs;
            logs.forEach(log => {
                const logElement = document.createElement('div');
                logElement.className = `log-entry log-${log.type || 'info'}`;
                logElement.textContent = `[${log.timestamp}] ${log.message}`;
                logsElement.appendChild(logElement);
            });
            if (autoScroll) {
                logsElement.scrollTop = logsElement.scrollHeight;
            }
        }
    });

    // Очистка логов
    clearLogsButton.addEventListener('click', function () {
        logs = [];
        logsElement.innerHTML = '';
        chrome.storage.local.set({ 'extension_logs': logs });
        addLog('Логи очищены');
    });

    // Переключение автопрокрутки
    toggleAutoScrollButton.addEventListener('click', function () {
        autoScroll = !autoScroll;
        this.textContent = `Автопрокрутка: ${autoScroll ? 'Вкл' : 'Выкл'}`;
    });

    // Слушатель сообщений
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (message.action === "log") {
            addLog(message.message, message.type || 'info');
        }
    });
});