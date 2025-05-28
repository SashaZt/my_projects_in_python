#!/bin/bash

# Обновление пакетов и установка зависимостей
sudo apt update -y
sudo apt upgrade -y
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Добавление GPG ключа Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Добавление репозитория Docker
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Установка Docker
sudo apt update -y
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Настройка автозапуска Docker
sudo systemctl enable docker
sudo systemctl start docker

# Добавление текущего пользователя в группу docker (чтобы не использовать sudo для docker команд)
sudo usermod -aG docker $USER

# Получение последней версии Docker Compose с GitHub API
DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep -Po '"tag_name": "\K.*?(?=")')

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Даем права на выполнение docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Проверка версий Docker и Docker Compose
docker --version
docker-compose --version

echo "Установка завершена! Перезагрузите или войдите заново, чтобы изменения вступили в силу."
