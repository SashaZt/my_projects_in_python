// static/js/streamers.js
document.addEventListener('DOMContentLoaded', function () {
    // Инициализация Socket.IO
    initSocketIO();
});

/**
 * Инициализация Socket.IO для получения обновлений в реальном времени
 */
function initSocketIO() {
    const socket = io({
        transports: ['polling'],
        upgrade: false
    });

    // Обработка подключения
    socket.on('connect', function () {
        console.log('Подключено к серверу Socket.IO');
        // Подключаемся к комнате со стримерами
        socket.emit('join_streamers_room');
    });

    // Обработка обновлений о стримерах
    socket.on('streamers_update', function (data) {
        updateStreamersTable(data);
    });

    // Обработка отключения
    socket.on('disconnect', function () {
        console.log('Отключено от сервера, переподключение...');
    });

    // Обработка ошибок
    socket.on('connect_error', function (error) {
        console.error('Ошибка подключения:', error);
    });
}

/**
 * Обновление таблицы стримеров
 */
function updateStreamersTable(data) {
    // Обновляем счетчики
    document.getElementById('total-streamers-count').textContent = data.total_streamers;
    document.getElementById('active-streamers-count').textContent = data.active_streamers;

    // Обновляем таблицу
    const tbody = document.querySelector('table tbody');
    if (!tbody) return;

    // Очищаем существующую таблицу
    tbody.innerHTML = '';

    // Добавляем строки для каждого стримера
    data.streamers.forEach(streamer => {
        const tr = document.createElement('tr');

        // Форматируем дату последней активности
        let lastActivity = '-';
        if (streamer.last_activity) {
            try {
                const date = new Date(streamer.last_activity);
                lastActivity = date.toLocaleString();
            } catch (e) {
                console.error('Ошибка форматирования даты:', e);
            }
        }

        // Формируем HTML строки
        tr.innerHTML = `
            <td>${streamer.name}</td>
            <td>${streamer.room_id || '-'}</td>
            <td>${streamer.cluster_name || '-'}</td>
            <td>
                ${streamer.status === 'Запущен'
                ? '<span class="status-active">Запущен</span>'
                : '<span class="status-inactive">Остановлен</span>'}
            </td>
            <td>${streamer.check_online} сек</td>
            <td>${lastActivity}</td>
            <td class="actions">
                <button onclick="window.location.href='/streamers/edit/${streamer.id}';">Редактировать</button>
                <button onclick="toggleStreamer(${streamer.id})">
                    ${streamer.status === 'Запущен' ? 'Остановить' : 'Запустить'}
                </button>
                <button class="danger" onclick="deleteStreamer(${streamer.id})">Удалить</button>
            </td>
        `;

        tbody.appendChild(tr);
    });
}

/**
 * Переключение статуса стримера
 */
function toggleStreamer(streamerId) {
    fetch(`/streamers/toggle/${streamerId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.status !== 'success') {
                alert('Ошибка при изменении статуса стримера');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Произошла ошибка при обработке запроса');
        });
}

/**
 * Удаление стримера
 */
function deleteStreamer(streamerId) {
    streamerToDelete = streamerId;
    document.getElementById('deleteModal').style.display = 'flex';
}