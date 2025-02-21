document.addEventListener('DOMContentLoaded', function () {
    const toggleButton = document.getElementById('toggleButton');
    const exportButton = document.getElementById('exportButton');
    const clearButton = document.getElementById('clearButton');
    const offersCountElement = document.getElementById('offersCount');
    const lastUpdateElement = document.getElementById('lastUpdate');
    const logsElement = document.getElementById('logs');
    const clearLogsButton = document.getElementById('clearLogs');
    const exportLogsButton = document.getElementById('exportLogs');
    const toggleAutoScrollButton = document.getElementById('toggleAutoScroll');

    let autoScroll = true;
    let logs = [];
    const MAX_LOGS = 1000;

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

    // Функция для скачивания файла
    function downloadObjectAsJson(exportObj, fileName) {
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(exportObj, null, 2));
        const downloadAnchorNode = document.createElement('a');
        downloadAnchorNode.setAttribute("href", dataStr);
        downloadAnchorNode.setAttribute("download", fileName);
        document.body.appendChild(downloadAnchorNode);
        downloadAnchorNode.click();
        downloadAnchorNode.remove();
    }

    // Обновление статистики
    function updateStats() {
        chrome.runtime.sendMessage({ action: "getStats" }, function (response) {
            if (response) {
                offersCountElement.textContent = response.accumulated || 0;
                lastUpdateElement.textContent = new Date().toLocaleString();
            }
        });
    }

    // Инициализация
    chrome.storage.local.get(['isEnabled', 'extension_logs'], function (result) {
        const isEnabled = result.isEnabled !== false;

        if (result.extension_logs) {
            logs = result.extension_logs;
            logs.forEach(log => {
                const logElement = document.createElement('div');
                logElement.className = `log-entry log-${log.type}`;
                logElement.textContent = `[${log.timestamp}] ${log.message}`;
                logsElement.appendChild(logElement);
            });
            if (autoScroll) {
                logsElement.scrollTop = logsElement.scrollHeight;
            }
        }

        updateButton(isEnabled);
        updateStats();
        addLog(`Расширение ${isEnabled ? 'включено' : 'выключено'}`);
    });

    // Обработчик переключения
    toggleButton.addEventListener('click', function () {
        chrome.storage.local.get(['isEnabled'], function (result) {
            const isEnabled = result.isEnabled !== false;
            const newState = !isEnabled;

            chrome.storage.local.set({ isEnabled: newState }, function () {
                updateButton(newState);
                addLog(`Состояние изменено на: ${newState ? 'включено' : 'выключено'}`);
            });
        });
    });

    // Экспорт накопленных данных
    exportButton.addEventListener('click', function () {
        chrome.runtime.sendMessage({ action: "exportOffers" }, function (response) {
            if (response.success && response.data) {
                const fileName = `allegro_offers_${new Date().toISOString()}.json`;
                downloadObjectAsJson(response.data, fileName);
                addLog(`Экспортировано ${response.count} офферов`);
                updateStats();
            } else {
                addLog(response.message || 'Ошибка при экспорте', 'error');
            }
        });
    });

    // Очистка логов
    clearLogsButton.addEventListener('click', function () {
        logs = [];
        logsElement.innerHTML = '';
        chrome.storage.local.set({ 'extension_logs': logs });
        addLog('Логи очищены');
    });

    // Экспорт логов
    exportLogsButton.addEventListener('click', function () {
        const blob = new Blob([logs.map(log =>
            `[${log.timestamp}] [${log.type}] ${log.message}`).join('\n')],
            { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `allegro_parser_logs_${new Date().toISOString()}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    });

    // Переключение автопрокрутки
    toggleAutoScrollButton.addEventListener('click', function () {
        autoScroll = !autoScroll;
        this.textContent = `Автопрокрутка: ${autoScroll ? 'Вкл' : 'Выкл'}`;
    });

    function updateButton(isEnabled) {
        toggleButton.textContent = isEnabled ? 'Выключить' : 'Включить';
        toggleButton.style.backgroundColor = isEnabled ? '#ff4444' : '#44ff44';
    }

    // Слушаем сообщения
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (message.action === "log") {
            addLog(message.message, message.type || 'info');
        }
        if (message.action === "statsUpdate") {
            updateStats();
            addLog(`Добавлено ${message.stats.new} новых офферов (Всего: ${message.stats.accumulated})`);
        }
    });

    // Регулярное обновление статистики
    setInterval(updateStats, 5000);
});