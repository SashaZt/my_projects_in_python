# 📦 Tampermonkey-скрипт: Capture and Save All Requests

## 📝 Установка скрипта

1. Нажмите иконку Tampermonkey →  **Создать новый скрипт** .
2. Вставьте код скрипта (artifact_id: requests.js, версия `0.7`) в редактор, заменив шаблонный код.
3. Сохраните скрипт (Ctrl+S или **File** →  **Save** ).
4. Убедитесь, что скрипт включен (зеленый переключатель в «Панель управления»).

---

## 🚀 Использование скрипта

### Запуск перехвата

1. Перейдите на сайт (например, [https://salescenter.allegro.com](https://salescenter.allegro.com/)).
2. Откройте DevTools (F12 →  **Console** ).
3. Если требуется, введите `allow pasting` и нажмите Enter.
4. Введите команду:

```javascript
start_script()
```

Скрипт начнёт перехватывать все сетевые запросы. Перехват продолжается даже после перезагрузки страницы.

### Выполнение действий

Производите любые действия на сайте: отправка форм, переходы, создание кампаний и т.д.

Запросы сохраняются в `localStorage`:

* Метод (POST, GET и т.д.)
* URL
* Заголовки
* Тело запроса
* Query-параметры
* Временная метка

### Остановка и экспорт

Когда закончите:

```javascript
stop_script()
```

Скрипт сформирует JSON-файл (например, `network_requests_2025-05-06T12-34-56Z.json`) и скачает его в папку загрузок.

### Просмотр сохраненных запросов

```javascript
viewSavedRequests()
```

### Очистка без экспорта

```javascript
clearSavedRequests()
```

---

## 🌐 Настройка доменов

Скрипт работает на:

```text
https://salescenter.allegro.com/*
https://edge.salescenter.allegro.com/*
```

Чтобы изменить:

1. Tampermonkey → Панель управления → выберите скрипт →  **Редактировать** .
2. Измените строки `@match`. Примеры:

```javascript
// @match        https://example.com/*
// @match        https://*.example.com/*
// @match        https://example.com/api/*
```

3. Сохраните изменения (Ctrl+S).

---

## ⚙️ Настройка типов запросов

Чтобы ограничить перехват только `POST` и `GET`:

1. Откройте редактор скрипта.
2. Найдите `saveRequest` и добавьте фильтр:

```javascript
if (!['POST', 'GET'].includes(requestData.method.toUpperCase())) return;
```

---

## 🧩 Дополнительные настройки

### Фильтрация по URL

```javascript
if (!requestData.url.includes('/api/')) return;
```

### Сохранение кук

```javascript
requestData.cookies = document.cookie;
```

### Заголовки для fetch:

```javascript
headers: init.headers ? Object.fromEntries(new Headers(init.headers)) : { 'Accept': 'application/json' },
```

### Экспорт в CSV:

```javascript
window.exportSavedRequests = function() {
  ...
  // CSV генерация
};
```

### Включение логов:

```javascript
console.log('Запрос сохранен:', requestData);
```

### Отключение автозапуска:

Удалите:

```javascript
if (isCapturing) {
    window.start_script();
}
```

---

## 🖥️ Отслеживаемые домены

```text
https://salescenter.allegro.com/*
https://edge.salescenter.allegro.com/*
```

Добавьте другие через директиву `@match` в блоке `// ==UserScript==`.

---

## 📡 Перехватываемые запросы

* POST
* GET
* PUT
* DELETE
* и другие методы

Скрипт перехватывает запросы, отправленные через:

* `fetch`
* `XMLHttpRequest`
* формы (`form`)

---

> **Примечание:** Вы можете адаптировать скрипт под свои задачи, в том числе ограничить домены, методы или конкретные endpoint'ы.
