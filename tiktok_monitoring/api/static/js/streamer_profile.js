// // app / static / js / streamer_profile.js
// document.addEventListener('DOMContentLoaded', function () {
//     const streamerId = window.location.pathname.split('/').pop();

//     // Обработка вкладок
//     const tabs = document.querySelectorAll('.tab');
//     tabs.forEach(tab => {
//         tab.addEventListener('click', function () {
//             tabs.forEach(t => t.classList.remove('active'));
//             document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
//             this.classList.add('active');
//             const tabId = this.getAttribute('data-tab');
//             document.getElementById(tabId).classList.add('active');
//         });
//     });

//     // Обработчики выбора периода
//     document.getElementById('donations-period').addEventListener('change', function () {
//         loadDonationsData(this.value);
//     });

//     document.getElementById('donators-period').addEventListener('change', function () {
//         loadDonatorsData(this.value);
//     });

//     // Загрузка данных при загрузке страницы
//     loadStatistics();
//     loadDonationsData('all');
//     loadDonatorsData('all');
//     loadStreamsData();
// });

// async function loadStatistics() {
//     try {
//         const streamerId = window.location.pathname.split('/').pop();
//         const response = await fetch(`/streamers/api/profile/${streamerId}/stats`);
//         const data = await response.json();

//         const donationsContainer = document.getElementById('donations');
//         const statCards = donationsContainer.querySelectorAll('.stat-card');

//         const statMapping = [
//             { index: 0, dataKey: 'all_time' },
//             { index: 1, dataKey: 'month' },
//             { index: 2, dataKey: 'week' },
//             { index: 3, dataKey: 'today' }
//         ];

//         statMapping.forEach(({ index, dataKey }) => {
//             const card = statCards[index];
//             const valueEl = card.querySelector('.value');
//             const subtitleEl = card.querySelector('.subtitle');
//             const statData = data[dataKey];

//             if (statData) {
//                 valueEl.textContent = `$${statData.total_dollars.toFixed(2)}`;
//                 subtitleEl.textContent = `${statData.donation_count} донатов`;
//             }
//         });

//     } catch (error) {
//         console.error('Ошибка при загрузке статистики:', error);
//     }
// }
// // Функция загрузки данных о донатах
// async function loadDonationsData(period) {
//     try {
//         document.getElementById('donations-table').innerHTML = `
//                 <tr>
//                     <td colspan="7" class="text-center">Загрузка данных...</td>
//                 </tr>
//             `;

//         const response = await fetch(`/streamers/api/profile/${streamerId}/donations?period=${period}`);
//         const data = await response.json();

//         if (data.donations && data.donations.length > 0) {
//             let tableHTML = '';

//             data.donations.forEach(donation => {
//                 tableHTML += `
//                         <tr>
//                             <td>${donation.id}</td>
//                             <td>${new Date(donation.event_time).toLocaleString()}</td>
//                             <td>${donation.unique_id}</td>
//                             <td>${donation.gift_name}</td>
//                             <td>${donation.gift_count}</td>
//                             <td>${donation.diamond_count}</td>
//                             <td>$${(donation.diamond_count * donation.gift_count / 200).toFixed(2)}</td>
//                         </tr>
//                     `;
//             });

//             document.getElementById('donations-table').innerHTML = tableHTML;
//         } else {
//             document.getElementById('donations-table').innerHTML = `
//                     <tr>
//                         <td colspan="7" class="text-center">Нет данных за выбранный период</td>
//                     </tr>
//                 `;
//         }
//     } catch (error) {
//         console.error('Ошибка при загрузке донатов:', error);
//         document.getElementById('donations-table').innerHTML = `
//                 <tr>
//                     <td colspan="7" class="text-center">Ошибка при загрузке данных</td>
//                 </tr>
//             `;
//     }
// }

// // Функция загрузки данных о донатерах
// async function loadDonatorsData(period) {
//     try {
//         document.getElementById('donators-table').innerHTML = `
//                 <tr>
//                     <td colspan="6" class="text-center">Загрузка данных...</td>
//                 </tr>
//             `;

//         const response = await fetch(`/streamers/api/profile/${streamerId}/donators?period=${period}`);
//         const data = await response.json();

//         if (data.donators && data.donators.length > 0) {
//             let tableHTML = '';

//             data.donators.forEach((donator, index) => {
//                 tableHTML += `
//                         <tr>
//                             <td>${index + 1}</td>
//                             <td>${donator.unique_id}</td>
//                             <td>${donator.donation_count}</td>
//                             <td>${donator.gift_count}</td>
//                             <td>${donator.diamond_count}</td>
//                             <td>$${(donator.diamond_count / 200).toFixed(2)}</td>
//                         </tr>
//                     `;
//             });

//             document.getElementById('donators-table').innerHTML = tableHTML;
//         } else {
//             document.getElementById('donators-table').innerHTML = `
//                     <tr>
//                         <td colspan="6" class="text-center">Нет данных за выбранный период</td>
//                     </tr>
//                 `;
//         }
//     } catch (error) {
//         console.error('Ошибка при загрузке донатеров:', error);
//         document.getElementById('donators-table').innerHTML = `
//                 <tr>
//                     <td colspan="6" class="text-center">Ошибка при загрузке данных</td>
//                 </tr>
//             `;
//     }
// }

// // Функция загрузки данных о стримах
// async function loadStreamsData() {
//     try {
//         document.getElementById('streams-table').innerHTML = `
//                 <tr>
//                     <td colspan="7" class="text-center">Загрузка данных...</td>
//                 </tr>
//             `;

//         const response = await fetch(`/streamers/api/profile/${streamerId}/streams`);
//         const data = await response.json();

//         if (data.streams && data.streams.length > 0) {
//             let tableHTML = '';

//             data.streams.forEach(stream => {
//                 // Рассчитываем длительность стрима
//                 const startDate = new Date(stream.start_time);
//                 const endDate = stream.end_time ? new Date(stream.end_time) : null;
//                 let duration = '-';

//                 if (endDate) {
//                     const durationMs = endDate - startDate;
//                     const hours = Math.floor(durationMs / (1000 * 60 * 60));
//                     const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));
//                     duration = `${hours}ч ${minutes}м`;
//                 }

//                 tableHTML += `
//                         <tr>
//                             <td>${stream.id}</td>
//                             <td>${startDate.toLocaleString()}</td>
//                             <td>${endDate ? endDate.toLocaleString() : 'В процессе'}</td>
//                             <td>${duration}</td>
//                             <td>${stream.max_viewers || 0}</td>
//                             <td>${stream.total_diamonds || 0}</td>
//                             <td>${stream.total_gifts || 0}</td>
//                         </tr>
//                     `;
//             });

//             document.getElementById('streams-table').innerHTML = tableHTML;
//         } else {
//             document.getElementById('streams-table').innerHTML = `
//                     <tr>
//                         <td colspan="7" class="text-center">Нет данных по стримам</td>
//                     </tr>
//                 `;
//         }
//     } catch (error) {
//         console.error('Ошибка при загрузке стримов:', error);
//         document.getElementById('streams-table').innerHTML = `
//                 <tr>
//                     <td colspan="7" class="text-center">Ошибка при загрузке данных</td>
//                 </tr>
//             `;
//     }
// }


// // });
document.addEventListener('DOMContentLoaded', function () {
    // Получаем ID стримера из URL
    const streamerId = window.location.pathname.split('/').pop();

    // Обработка вкладок
    const tabs = document.querySelectorAll('.tab');

    tabs.forEach(tab => {
        tab.addEventListener('click', function () {
            // Убираем активный класс со всех вкладок
            tabs.forEach(t => t.classList.remove('active'));

            // Убираем активный класс со всех контентов
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });

            // Добавляем активный класс нажатой вкладке
            this.classList.add('active');

            // Показываем соответствующий контент
            const tabId = this.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
        });
    });

    // Обработчики изменения периода
    document.getElementById('donations-period').addEventListener('change', function () {
        loadDonationsData(this.value);
    });

    document.getElementById('donators-period').addEventListener('change', function () {
        loadDonatorsData(this.value);
    });
    // Функция загрузки общей статистики
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

                if (statData && valueEl && subtitleEl) {
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

    // Инициализация - загружаем данные
    loadStatistics();
    loadDonationsData('all');
    loadDonatorsData('all');
    loadStreamsData();

});