Вот набор curl запросов для проверки записанных данных в вашем API:

### * Получение пользователя по TikTok ID

curl -k -X GET "https://localhost:5000/api/users/7312401215441126406" -H "Content-Type: application/json"

Получение списка всех пользователей

curl -k -X GET "https://localhost:5000/api/users/" -H "Content-Type: application/json"

3. Получение статистики пользователя

# Замените на фактический ID пользователя из базы данных

curl -k -X GET "https://localhost:5000/api/stats/user-stats/1" -H "Content-Type: application/json"

4. Получение истории прямых трансляций

# Замените на фактический ID пользователя

curl -k -X GET "https://localhost:5000/api/live/streams/1" -H "Content-Type: application/json"

5. Получение дневной аналитики

# Замените на фактический ID пользователя

curl -k -X GET "https://localhost:5000/api/live/analytics/1" -H "Content-Type: application/json"

6. Получение отфильтрованных данных по периоду (для прямых трансляций)

# Замените и диапазон дат

curl -k -X GET "https://localhost:5000/api/live/streams/1?from_date=2025-03-01T00:00:00Z&to_date=2025-04-01T23:59:59Z" -H "Content-Type: application/json"

7. Получение отфильтрованных данных по периоду (для аналитики)

# Замените и диапазон дат

curl -k -X GET "https://localhost:5000/api/live/analytics/1?from_date=2025-03-01&to_date=2025-04-01" -H "Content-Type: application/json"

8. Проверка работоспособности API

curl -k -X GET "https://localhost:5000/health" -H "Content-Type: application/json"

Примечания:

Параметр -k (или --insecure) используется для того, чтобы curl не проверял SSL-сертификат. Это полезно для локальной разработки, но не рекомендуется для продакшена.

Может потребоваться замена localhost:5000 на фактический адрес вашего API, если он развернут на другом хосте или порту.

В примерах предполагается, что ID пользователя в базе данных - 1. Если фактический ID отличается, замените его соответствующим значением.

Для фильтрации по датам используются разные форматы:

Для временных меток (timestamp) используется формат ISO 8601 (например, 2025-03-01T00:00:00Z)

Для дат используется формат ISO 8601 без времени (например, 2025-03-01)

Если ваш API требует аутентификации, вам нужно будет добавить соответствующие заголовки, например:

bashCopy-H "Authorization: Bearer your_token_here"

Эти команды curl могут быть полезны как для ручного тестирования API, так и для включения в скрипты автоматизации или документацию.
