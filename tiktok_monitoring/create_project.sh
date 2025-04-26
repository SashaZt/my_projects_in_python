#!/bin/bash

# Создание основной директории
mkdir -p tiktok_dashboard

# Создание структуры директорий и файлов в app/
mkdir -p tiktok_dashboard/app/{models,services,routes,websockets,static/{js,css}}
touch tiktok_dashboard/app/__init__.py
touch tiktok_dashboard/app/main.py
touch tiktok_dashboard/app/config.py
touch tiktok_dashboard/app/database.py
touch tiktok_dashboard/app/models/__init__.py
touch tiktok_dashboard/app/models/gift.py
touch tiktok_dashboard/app/models/streamer.py
touch tiktok_dashboard/app/models/cluster.py
touch tiktok_dashboard/app/services/__init__.py
touch tiktok_dashboard/app/services/statistics.py
touch tiktok_dashboard/app/services/monitoring.py
touch tiktok_dashboard/app/routes/__init__.py
touch tiktok_dashboard/app/routes/dashboard.py
touch tiktok_dashboard/app/routes/streamers.py
touch tiktok_dashboard/app/routes/clusters.py
touch tiktok_dashboard/app/routes/gifts.py
touch tiktok_dashboard/app/websockets/__init__.py
touch tiktok_dashboard/app/websockets/dashboard.py
touch tiktok_dashboard/app/static/js/dashboard.js
touch tiktok_dashboard/app/static/css/styles.css

# Создание директории templates и файлов
mkdir -p tiktok_dashboard/templates
touch tiktok_dashboard/templates/base.html
touch tiktok_dashboard/templates/dashboard.html
touch tiktok_dashboard/templates/streamers.html
touch tiktok_dashboard/templates/clusters.html
touch tiktok_dashboard/templates/gifts.html

# Создание requirements.txt
touch tiktok_dashboard/requirements.txt

echo "Структура проекта создана успешно!"