#!/bin/bash

# Перед запуском этого скрипта выполните следующие команды для установки прав на выполнение и запуска:
# chmod +x install_docker.sh
# ./install_docker.sh

# Устанавливаем временную зону на Киев
echo "Настройка времени на Киев..."
sudo timedatectl set-timezone Europe/Kiev
echo "Текущее время и временная зона:"
timedatectl

# Обновляем пакетный индекс
sudo apt-get update

# Устанавливаем необходимые зависимости
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common

# Добавляем Docker GPG ключ
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Добавляем Docker репозиторий
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Обновляем пакетный индекс еще раз
sudo apt-get update

# Устанавливаем Docker CE
sudo apt-get install -y docker-ce

# Проверяем установку Docker
docker --version

# Устанавливаем Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep -oP '"tag_name": "\K[^"]*')/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Делаем Docker Compose исполняемым
sudo chmod +x /usr/local/bin/docker-compose

# Проверяем установку Docker Compose
docker-compose --version