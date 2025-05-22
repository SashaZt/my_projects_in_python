
// // dashboard.js - Обработка обновлений дашборда в реальном времени с Socket.IO

// document.addEventListener('DOMContentLoaded', function () {
//     // Инициализация Socket.IO
//     initSocketIO();

//     // Настройка интерактивных элементов
//     setupInteractions();
// });

// /**
//  * Инициализация Socket.IO для получения обновлений в реальном времени
//  */
// function initSocketIO() {
//     const socket = io({
//         transports: ['polling'],
//         upgrade: false
//     });

//     // Обработка подключения
//     socket.on('connect', function () {
//         console.log('Подключено к серверу');
//     });

//     // Обработка полученных обновлений
//     socket.on('dashboard_update', function (data) {
//         updateDashboard(data);
//     });

//     // Обработка отключения
//     socket.on('disconnect', function () {
//         console.log('Отключено от сервера, переподключение...');
//     });

//     // Обработка ошибок
//     socket.on('connect_error', function (error) {
//         console.error('Ошибка подключения:', error);
//     });
// }

// /**
//  * Обновление элементов дашборда данными, полученными с сервера
//  */
// function updateDashboard(data) {
//     // Обновление статистики
//     updateElement("total-gifts", data.total_gifts_today);
//     updateElement("percent-total-gifts", data.percent_total_gifts_today);

//     updateElement("total-diamonds", formatNumber(data.total_diamonds_today));
//     updateElement("percent-total-diamonds", data.percent_total_diamonds);

//     updateElement("total-dollars", formatCurrency(data.total_dollars_today));
//     updateElement("percent-total-dollars", data.percent_total_dollars);

//     updateElement("week-gifts", formatNumber(data.last_week_gift));
//     updateElement("percent-week", data.percent_week);

//     updateElement("month-gifts", formatNumber(data.last_month_gift));
//     updateElement("percent-month", data.percent_month);

//     updateElement("tracked-streamers", data.tracked_streamers);
//     updateElement("total-streamers", `из ${data.count_all}`);

//     updateElement("unique-donators", formatNumber(data.total_unique_donators));
//     updateElement("donators-week", formatNumber(data.donators_week));

//     // Обновление списка последних подарков
//     updateGiftsList(data.recent_gifts);
// }

// /**
//  * Обновление содержимого HTML элемента
//  */
// function updateElement(id, value) {
//     const element = document.getElementById(id);
//     if (element && value !== undefined) {
//         element.textContent = value;
//     }
// }

// /**
//  * Обновление списка подарков
//  */
// function updateGiftsList(gifts) {
//     const giftsList = document.getElementById("gifts-list");
//     if (!giftsList || !Array.isArray(gifts)) return;

//     // Очищаем текущий список
//     giftsList.innerHTML = "";

//     // Добавляем новые элементы
//     gifts.forEach(gift => {
//         const item = document.createElement("div");
//         item.classList.add("gift-item");

//         const time = new Date(gift.event_time).toLocaleTimeString();
//         const dollarAmount = (gift.diamondCount / 200).toFixed(2);

//         item.innerHTML = `
//             <span class="gift-time">${time}</span>
//             <span class="gift-user">${gift.uniqueId}</span> подарил 
//             <span class="gift-name">${gift.giftName} x${gift.giftCount}</span> 
//             (<span class="gift-price">${gift.diamondCount} 💎 / $${dollarAmount}</span>) 
//             стримеру <span class="gift-streamer">${gift.receiverUniqueId}</span>
//         `;

//         giftsList.appendChild(item);
//     });
// }

// /**
//  * Настройка интерактивных элементов на странице
//  */
// function setupInteractions() {
//     // При необходимости можно добавить обработчики событий для различных кнопок и форм
// }

// /**
//  * Форматирование числа с разделителями разрядов
//  */
// function formatNumber(number) {
//     if (number === undefined || number === null) return "0";
//     return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
// }

// /**
//  * Форматирование денежной суммы
//  */
// function formatCurrency(amount) {
//     if (amount === undefined || amount === null) return "$0.00";
//     return "$" + (Math.round(amount * 100) / 100).toFixed(2);
// }
// app/static/js/dashboard.js
// Обработка обновлений дашборда в реальном времени с Socket.IO

// // app/static/js/dashboard.js
document.addEventListener('DOMContentLoaded', function () {
    // Инициализация Socket.IO
    initSocketIO();

    // Настройка интерактивных элементов
    setupInteractions();
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
    });

    // Обработка полученных обновлений
    socket.on('dashboard_stats', function (data) {
        updateDashboard(data);
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
 * Обновление элементов дашборда данными, полученными с сервера
 */
function updateDashboard(data) {
    // Обновление статистики
    updateElement("total-gifts", data.total_gifts_today);
    updateElement("percent-total-gifts", calculatePercentChange(data.total_gifts_today, data.total_gifts_yesterday));

    updateElement("total-diamonds", formatNumber(data.total_diamonds_today));
    updateElement("percent-total-diamonds", calculatePercentChange(data.total_diamonds_today, data.total_diamonds_yesterday));

    updateElement("total-dollars", formatCurrency(data.total_dollars_today));
    updateElement("percent-total-dollars", calculatePercentChange(data.total_dollars_today, data.total_dollars_yesterday));

    updateElement("week-gifts", formatNumber(data.last_week_gifts));
    updateElement("percent-week", calculatePercentChange(data.last_week_gifts, data.last_week_prev_gifts));

    updateElement("month-gifts", formatNumber(data.last_month_gifts));
    updateElement("percent-month", calculatePercentChange(data.last_month_gifts, data.last_month_prev_gifts));

    updateElement("tracked-streamers", data.tracked_streamers);
    updateElement("total-streamers", `из ${data.total_streamers || 0}`);

    updateElement("unique-donators", formatNumber(data.unique_donators_total));
    updateElement("donators-week", `на этой неделе: ${formatNumber(data.unique_donators_week)}`);

    // Обновление списка последних подарков (если данные предоставлены)
    if (data.recent_gifts) {
        updateGiftsList(data.recent_gifts);
    }
}

/**
 * Обновление содержимого HTML элемента
 */
function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element && value !== undefined && value !== null) {
        element.textContent = value;
    } else if (element) {
        element.textContent = '0'; // Значение по умолчанию
    }
}

/**
 * Обновление списка подарков
 */
function updateGiftsList(gifts) {
    const giftsList = document.getElementById("gifts-list");
    if (!giftsList || !Array.isArray(gifts)) return;

    // Очищаем текущий список
    giftsList.innerHTML = "";

    // Добавляем новые элементы
    gifts.forEach(gift => {
        const item = document.createElement("div");
        item.classList.add("gift-item");

        const time = new Date(gift.event_time).toLocaleTimeString();
        const dollarAmount = (gift.diamond_count * gift.gift_count / 200).toFixed(2);

        item.innerHTML = `
            <span class="gift-time">${time}</span>
            <span class="gift-user">${gift.unique_id}</span> подарил 
            <span class="gift-name">${gift.gift_name} x${gift.gift_count}</span> 
            (<span class="gift-price">${gift.diamond_count * gift.gift_count} 💎 / $${dollarAmount}</span>) 
            стримеру <span class="gift-streamer">${gift.receiver_unique_id}</span>
        `;

        giftsList.appendChild(item);
    });
}

/**
 * Настройка интерактивных элементов на странице
 */
function setupInteractions() {
    // При необходимости можно добавить обработчики событий для различных кнопок и форм
}

/**
 * Форматирование числа с разделителями разрядов
 */
function formatNumber(number) {
    if (number === undefined || number === null) return "0";
    return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
}

/**
 * Форматирование денежной суммы
 */
function formatCurrency(amount) {
    if (amount === undefined || amount === null) return "$0.00";
    return "$" + (Math.round(amount * 100) / 100).toFixed(2);
}

/**
 * Вычисление процентного изменения
 */
function calculatePercentChange(current, previous) {
    if (current === undefined || previous === undefined || previous === 0) return "";
    const change = ((current - previous) / previous * 100).toFixed(1);
    return change > 0 ? `+${change}%` : `${change}%`;
}