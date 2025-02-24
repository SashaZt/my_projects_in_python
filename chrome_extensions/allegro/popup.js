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
    const startPaginationButton = document.getElementById('startPaginationButton');
    const stopPaginationButton = document.getElementById('stopPaginationButton');
    // Добавляем обработку настроек планировщика
    const scheduleTimeInput = document.getElementById('scheduleTime');
    const scheduleDaysSelect = document.getElementById('scheduleDays');
    const saveScheduleButton = document.getElementById('saveSchedule');
    const toggleScheduleButton = document.getElementById('toggleSchedule');
    const scheduleStatusSpan = document.getElementById('scheduleStatus');
    const nextRunSpan = document.getElementById('nextRun');

    let autoScroll = true;
    let logs = [];
    const MAX_LOGS = 1000;
    document.getElementById('processAllShops').addEventListener('click', function () {
        chrome.runtime.sendMessage({ action: "startShopsProcessing" }, function (response) {
            if (response.status === "started") {
                addLog('Запущена обработка всех магазинов');
            }
        });
    });
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
    // Форматирование даты
    function formatNextRun(dateStr) {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        return date.toLocaleString();
    }

    // Загрузка настроек планировщика
    function loadSchedulerSettings() {
        chrome.runtime.sendMessage({ action: "getSchedulerSettings" }, function (settings) {
            if (settings) {
                scheduleTimeInput.value = settings.time || "08:00";

                // Устанавливаем выбранные дни
                Array.from(scheduleDaysSelect.options).forEach(option => {
                    option.selected = settings.days.includes(Number(option.value));
                });

                // Обновляем статус
                scheduleStatusSpan.textContent = settings.enabled ? 'Включен' : 'Выключен';
                scheduleStatusSpan.className = settings.enabled ? 'status-enabled' : 'status-disabled';
                toggleScheduleButton.textContent = settings.enabled ? 'Выключить планировщик' : 'Включить планировщик';

                // Обновляем время следующего запуска
                nextRunSpan.textContent = formatNextRun(settings.nextRun);
            }
        });
    }

    // Сохранение настроек
    async function saveSettings() {
        const selectedDays = Array.from(scheduleDaysSelect.selectedOptions).map(opt => Number(opt.value));

        const settings = {
            time: scheduleTimeInput.value,
            days: selectedDays
        };

        addLog('Сохранение настроек планировщика...');

        chrome.runtime.sendMessage({
            action: "saveSchedulerSettings",
            settings: settings
        }, function (response) {
            if (response.success) {
                addLog('Настройки планировщика сохранены');
                loadSchedulerSettings(); // Перезагружаем для обновления UI
            } else {
                addLog('Ошибка при сохранении настроек: ' + (response.error || 'Unknown error'), 'error');
            }
        });
    }

    // Переключение состояния планировщика
    async function toggleScheduler() {
        chrome.runtime.sendMessage({
            action: "saveSchedulerSettings",
            settings: {
                enabled: scheduleStatusSpan.textContent === 'Выключен'
            }
        }, function (response) {
            if (response.success) {
                loadSchedulerSettings();
                addLog(`Планировщик ${scheduleStatusSpan.textContent === 'Выключен' ? 'включен' : 'выключен'}`);
            }
        });
    }

    // Добавляем обработчики событий
    saveScheduleButton.addEventListener('click', saveSettings);
    toggleScheduleButton.addEventListener('click', toggleScheduler);

    // Загружаем настройки при открытии popup
    loadSchedulerSettings();

    // Обновляем настройки каждые 30 секунд
    setInterval(loadSchedulerSettings, 30000);
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

    // В основном слушателе сообщений добавим обработку downloadData
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (message.action === "log") {
            addLog(message.message, message.type || 'info');
        }
        else if (message.action === "statsUpdate") {
            updateStats();
            addLog(`Добавлено ${message.stats.new} новых офферов (Всего: ${message.stats.accumulated})`);
        }
        else if (message.action === "downloadData") {
            
            if (message.data && message.fileName) {
                // Используем имя файла из сообщения
                downloadObjectAsJson(message.data, message.fileName);
                addLog(`Скачан файл: ${message.fileName}`);
            } else if (message.data) {
                // Если имя файла не передано, используем резервный вариант
                const fileName = `allegro_offers_${new Date().toISOString().split('.')[0].replace(/:/g, '-')}.json`;
                downloadObjectAsJson(message.data, fileName);
                addLog(`Скачан файл: ${fileName}`);
            }
        }
    });
    // Обработчики для кнопок пагинации
    startPaginationButton.addEventListener('click', function () {
        chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
            if (tabs[0]) {
                chrome.tabs.sendMessage(tabs[0].id, {
                    action: "startPagination"
                }, function (response) {
                    if (chrome.runtime.lastError) {
                        addLog('Ошибка запуска пагинации: ' + chrome.runtime.lastError.message, 'error');
                    } else {
                        addLog('Запущена автоматическая пагинация');
                    }
                });
            }
        });
    });

    stopPaginationButton.addEventListener('click', function () {
        chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
            if (tabs[0]) {
                chrome.tabs.sendMessage(tabs[0].id, {
                    action: "stopPagination"
                }, function (response) {
                    if (chrome.runtime.lastError) {
                        addLog('Ошибка остановки пагинации: ' + chrome.runtime.lastError.message, 'error');
                    } else {
                        addLog('Пагинация остановлена');
                    }
                });
            }
        });
    });
    // Функция для принудительного внедрения content script
    async function injectContentScript(tabId) {
        try {
            await chrome.scripting.executeScript({
                target: { tabId: tabId },
                files: ['content.js']
            });
            return true;
        } catch (error) {
            console.error('Failed to inject content script:', error);
            return false;
        }
    }

    // Модифицированная функция отправки сообщения
    async function sendMessageToTab(tabId, message) {
        try {
            return await chrome.tabs.sendMessage(tabId, message);
        } catch (error) {
            if (error.message.includes('Receiving end does not exist')) {
                // Пробуем внедрить скрипт
                const injected = await injectContentScript(tabId);
                if (injected) {
                    // Даем время на инициализацию
                    await new Promise(resolve => setTimeout(resolve, 100));
                    // Пробуем отправить сообщение снова
                    return await chrome.tabs.sendMessage(tabId, message);
                }
            }
            throw error;
        }
    }

    // Обновляем обработчики кнопок пагинации
    startPaginationButton.addEventListener('click', async function () {
        try {
            const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
            if (!tabs[0]) {
                addLog('Активная вкладка не найдена', 'error');
                return;
            }

            await sendMessageToTab(tabs[0].id, { action: "startPagination" });
            addLog('Запущена автоматическая пагинация');
        } catch (error) {
            addLog('Ошибка запуска пагинации: ' + error.message, 'error');
        }
    });

    stopPaginationButton.addEventListener('click', async function () {
        try {
            const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
            if (!tabs[0]) {
                addLog('Активная вкладка не найдена', 'error');
                return;
            }

            await sendMessageToTab(tabs[0].id, { action: "stopPagination" });
            addLog('Пагинация остановлена');
        } catch (error) {
            addLog('Ошибка остановки пагинации: ' + error.message, 'error');
        }
    });
    // Регулярное обновление статистики
    setInterval(updateStats, 5000);
});