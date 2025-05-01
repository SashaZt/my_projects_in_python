document.addEventListener('DOMContentLoaded', function () {
    const streamerId = window.location.pathname.split('/').pop();

    // Обработка вкладок
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', function () {
            tabs.forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            this.classList.add('active');
            const tabId = this.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
        });
    });

    // Обработчики выбора периода
    document.getElementById('donations-period').addEventListener('change', function () {
        loadDonationsData(this.value);
    });

    document.getElementById('donators-period').addEventListener('change', function () {
        loadDonatorsData(this.value);
    });

    // Загрузка данных при загрузке страницы
    loadStatistics();
    loadDonationsData('all');
    loadDonatorsData('all');
    loadStreamsData();
});

async function loadStatistics() {
    try {
        const streamerId = window.location.pathname.split('/').pop();
        const response = await fetch(`/streamers/api/profile/${streamerId}/stats`);
        const data = await response.json();

        const donationsContainer = document.getElementById('donations');
        const statCards = donationsContainer.querySelectorAll('.stat-card');

        const statMapping = [
            { index: 0, dataKey: 'all_time' },
            { index: 1, dataKey: 'month' },
            { index: 2, dataKey: 'week' },
            { index: 3, dataKey: 'today' }
        ];

        statMapping.forEach(({ index, dataKey }) => {
            const card = statCards[index];
            const valueEl = card.querySelector('.value');
            const subtitleEl = card.querySelector('.subtitle');
            const statData = data[dataKey];

            if (statData) {
                valueEl.textContent = `$${statData.total_dollars.toFixed(2)}`;
                subtitleEl.textContent = `${statData.donation_count} донатов`;
            }
        });

    } catch (error) {
        console.error('Ошибка при загрузке статистики:', error);
    }
}
// Функция загрузки данных о донатах
async function loadDonationsData(period) {
    try {
        document.getElementById('donations-table').innerHTML = `
                <tr>
                    <td colspan="7" class="text-center">Загрузка данных...</td>
                </tr>
            `;

        const response = await fetch(`/streamers/api/profile/${streamerId}/donations?period=${period}`);
        const data = await response.json();

        if (data.donations && data.donations.length > 0) {
            let tableHTML = '';

            data.donations.forEach(donation => {
                tableHTML += `
                        <tr>
                            <td>${donation.id}</td>
                            <td>${new Date(donation.event_time).toLocaleString()}</td>
                            <td>${donation.unique_id}</td>
                            <td>${donation.gift_name}</td>
                            <td>${donation.gift_count}</td>
                            <td>${donation.diamond_count}</td>
                            <td>$${(donation.diamond_count * donation.gift_count / 200).toFixed(2)}</td>
                        </tr>
                    `;
            });

            document.getElementById('donations-table').innerHTML = tableHTML;
        } else {
            document.getElementById('donations-table').innerHTML = `
                    <tr>
                        <td colspan="7" class="text-center">Нет данных за выбранный период</td>
                    </tr>
                `;
        }
    } catch (error) {
        console.error('Ошибка при загрузке донатов:', error);
        document.getElementById('donations-table').innerHTML = `
                <tr>
                    <td colspan="7" class="text-center">Ошибка при загрузке данных</td>
                </tr>
            `;
    }
}

// Функция загрузки данных о донатерах
async function loadDonatorsData(period) {
    try {
        document.getElementById('donators-table').innerHTML = `
                <tr>
                    <td colspan="6" class="text-center">Загрузка данных...</td>
                </tr>
            `;

        const response = await fetch(`/streamers/api/profile/${streamerId}/donators?period=${period}`);
        const data = await response.json();

        if (data.donators && data.donators.length > 0) {
            let tableHTML = '';

            data.donators.forEach((donator, index) => {
                tableHTML += `
                        <tr>
                            <td>${index + 1}</td>
                            <td>${donator.unique_id}</td>
                            <td>${donator.donation_count}</td>
                            <td>${donator.gift_count}</td>
                            <td>${donator.diamond_count}</td>
                            <td>$${(donator.diamond_count / 200).toFixed(2)}</td>
                        </tr>
                    `;
            });

            document.getElementById('donators-table').innerHTML = tableHTML;
        } else {
            document.getElementById('donators-table').innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center">Нет данных за выбранный период</td>
                    </tr>
                `;
        }
    } catch (error) {
        console.error('Ошибка при загрузке донатеров:', error);
        document.getElementById('donators-table').innerHTML = `
                <tr>
                    <td colspan="6" class="text-center">Ошибка при загрузке данных</td>
                </tr>
            `;
    }
}

// Функция загрузки данных о стримах
async function loadStreamsData() {
    try {
        document.getElementById('streams-table').innerHTML = `
                <tr>
                    <td colspan="7" class="text-center">Загрузка данных...</td>
                </tr>
            `;

        const response = await fetch(`/streamers/api/profile/${streamerId}/streams`);
        const data = await response.json();

        if (data.streams && data.streams.length > 0) {
            let tableHTML = '';

            data.streams.forEach(stream => {
                // Рассчитываем длительность стрима
                const startDate = new Date(stream.start_time);
                const endDate = stream.end_time ? new Date(stream.end_time) : null;
                let duration = '-';

                if (endDate) {
                    const durationMs = endDate - startDate;
                    const hours = Math.floor(durationMs / (1000 * 60 * 60));
                    const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));
                    duration = `${hours}ч ${minutes}м`;
                }

                tableHTML += `
                        <tr>
                            <td>${stream.id}</td>
                            <td>${startDate.toLocaleString()}</td>
                            <td>${endDate ? endDate.toLocaleString() : 'В процессе'}</td>
                            <td>${duration}</td>
                            <td>${stream.max_viewers || 0}</td>
                            <td>${stream.total_diamonds || 0}</td>
                            <td>${stream.total_gifts || 0}</td>
                        </tr>
                    `;
            });

            document.getElementById('streams-table').innerHTML = tableHTML;
        } else {
            document.getElementById('streams-table').innerHTML = `
                    <tr>
                        <td colspan="7" class="text-center">Нет данных по стримам</td>
                    </tr>
                `;
        }
    } catch (error) {
        console.error('Ошибка при загрузке стримов:', error);
        document.getElementById('streams-table').innerHTML = `
                <tr>
                    <td colspan="7" class="text-center">Ошибка при загрузке данных</td>
                </tr>
            `;
    }
}

// async function loadStatistics() {
//     try {
//         console.log('Начинаю загрузку статистики...');

//         // Получаем ID стримера из URL
//         const streamerId = window.location.pathname.split('/').pop();
//         if (!streamerId) {
//             throw new Error('Не удалось получить ID стримера из URL');
//         }

//         // Запрос данных с API
//         const response = await fetch(`/streamers/api/profile/${streamerId}/stats`);
//         if (!response.ok) {
//             throw new Error(`HTTP ошибка! Статус: ${response.status}`);
//         }

//         const data = await response.json();
//         console.log('Полученные данные:', data);

//         // Поиск контейнера статистики
//         const donationsContainer = document.getElementById('donations');
//         if (!donationsContainer) {
//             throw new Error('Не найден контейнер статистики с id="donations"');
//         }

//         // Поиск всех карточек статистики
//         const statCards = donationsContainer.querySelectorAll('.stat-card');
//         console.log(`Найдено ${statCards.length} карточек статистики`);

//         // Маппинг карточек и данных
//         const statMapping = [
//             {
//                 index: 0,
//                 dataKey: 'all_time',
//                 logMsg: 'За все время'
//             },
//             {
//                 index: 1,
//                 dataKey: 'month',
//                 logMsg: 'За текущий месяц'
//             },
//             {
//                 index: 2,
//                 dataKey: 'week',
//                 logMsg: 'За текущую неделю'
//             },
//             {
//                 index: 3,
//                 dataKey: 'today',
//                 logMsg: 'За сегодня'
//             }
//         ];

//         // Обновление карточек
//         statMapping.forEach(({ index, dataKey, logMsg }) => {
//             const card = statCards[index];
//             if (!card) return;

//             const valueEl = card.querySelector('.value');
//             const subtitleEl = card.querySelector('.subtitle');

//             if (!valueEl || !subtitleEl) {
//                 console.warn(`В карточке "${logMsg}" отсутствуют элементы .value или .subtitle`);
//                 return;
//             }

//             const statData = data[dataKey];
//             if (!statData) {
//                 console.warn(`Нет данных для статистики "${logMsg}"`);
//                 return;
//             }

//             valueEl.textContent = `$${statData.total_dollars.toFixed(2)}`;
//             subtitleEl.textContent = `${statData.donation_count} донатов`;
//             console.log(`Обновлена статистика "${logMsg}"`);
//         });

//     } catch (error) {
//         console.error('Критическая ошибка при загрузке статистики:', error);
//         // Резервный метод обновления
//         console.log('Попытка обновления через updateStatsDirect...');
//         updateStatsDirect();
//     }
// }


    // // Функция для прямого обновления значений статистики (для отладки)
    // function updateStatsDirect() {
    //     const statCards = document.querySelectorAll('#donations .stat-card');
    //     console.log(`Найдено ${statCards.length} карточек статистики для прямого обновления`);

    //     const stats = [
    //         { value: '$168.32', subtitle: '215 донатов' },  // За все время
    //         { value: '$168.32', subtitle: '215 донатов' },  // За месяц
    //         { value: '$149.09', subtitle: '177 донатов' },  // За неделю
    //         { value: '$4.92', subtitle: '30 донатов' }      // За сегодня
    //     ];

    //     for (let i = 0; i < Math.min(statCards.length, stats.length); i++) {
    //         const valueEl = statCards[i].querySelector('.value');
    //         const subtitleEl = statCards[i].querySelector('.subtitle');

    //         if (valueEl && subtitleEl) {
    //             valueEl.innerHTML = stats[i].value;
    //             subtitleEl.innerHTML = stats[i].subtitle;
    //             console.log(`Карточка ${i + 1} обновлена напрямую`);
    //         } else {
    //             console.error(`Не найдены элементы в карточке ${i + 1}`);
    //         }
    //     }
    // }

    // Инициализация - загружаем данные
    // loadDonationsData('all');
    // loadDonatorsData('all');
    // loadStreamsData();
    // loadStatistics();

    // // Сначала загружаем с задержкой для уверенности
    // setTimeout(() => {
    //     console.log('Загрузка статистики с задержкой...');
    //     loadStatistics();

    //     // Если статистика не загрузилась, пробуем прямое обновление через 2 секунды
    //     setTimeout(() => {
    //         // Проверяем, обновились ли значения
    //         const firstValue = document.querySelector('#donations .stat-card:first-child .value');
    //         if (firstValue && firstValue.textContent === '$0') {
    //             console.log('Статистика не загрузилась автоматически, пробуем прямое обновление...');
    //             updateStatsDirect();
    //         }
    //     }, 2000);
    // }, 1000);

    // Также пробуем загрузить сразу

});