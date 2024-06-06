#!/bin/bash

# Переменные для подключения к серверу
USER="root"
SERVER="164.92.240.39"
EMAIL="	a.zinchyk83@gmail.com"
PORT="22222"

# Изменение порта SSH
sed -i "s/^Port .*/Port $PORT/" /etc/ssh/sshd_config

# Включение входа по сертификату и отключение входа по паролю
sed -i -e '/^PasswordAuthentication / s/=.*/= no/' /etc/ssh/sshd_config
sed -i -e '/^PubkeyAuthentication / s/=.*/= yes/' /etc/ssh/sshd_config

# Перезапуск службы SSH
# systemctl restart ssh

# Создание SSH ключа и добавление на сервер
ssh-keygen -t rsa -b 4096 -C "$EMAIL" -f ~/.ssh/id_rsa -q -N ""
cat ~/.ssh/id_rsa.pub | ssh "$USER@$SERVER" -p "$PORT" "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"

