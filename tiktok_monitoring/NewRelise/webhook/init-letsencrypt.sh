#!/bin/bash

if ! [ -x "$(command -v docker-compose)" ]; then
  echo 'Error: docker-compose is not installed.' >&2
  exit 1
fi

# Замените на ваш домен и email
domains=(tikspy.cc)
rsa_key_size=4096
email="unilivetech@proton.me" # Используется для уведомлений о продлении
staging=0 # Установите 1 для тестирования (избегайте лимитов Let's Encrypt)

# Создаем необходимые директории
mkdir -p data/certbot/conf data/certbot/www

echo "### Создание фиктивных сертификатов для запуска Nginx..."
for domain in "${domains[@]}"; do
  mkdir -p "data/certbot/conf/live/$domain"
  mkdir -p "data/certbot/conf/archive/$domain"
  
  # Создаем фиктивные сертификаты, чтобы Nginx мог запуститься
  openssl req -x509 -nodes -newkey rsa:$rsa_key_size -days 1 \
    -keyout "data/certbot/conf/live/$domain/privkey.pem" \
    -out "data/certbot/conf/live/$domain/fullchain.pem" \
    -subj "/CN=localhost"
  
  # Устанавливаем корректные права
  chmod 644 "data/certbot/conf/live/$domain/privkey.pem"
done

echo "### Запуск Nginx..."
docker-compose up --force-recreate -d nginx

echo "### Удаление фиктивных сертификатов..."
for domain in "${domains[@]}"; do
  rm -Rf "data/certbot/conf/live/$domain"
  rm -Rf "data/certbot/conf/archive/$domain"
  rm -Rf "data/certbot/conf/renewal/$domain.conf"
done

echo "### Получение сертификатов Let's Encrypt..."

# Выбираем флаги certbot в зависимости от режима (тестовый или боевой)
staging_arg=""
if [ $staging -eq 1 ]; then
  staging_arg="--staging"
fi

domain_args=""
for domain in "${domains[@]}"; do
  domain_args="$domain_args -d $domain"
done

# Запускаем certbot для получения сертификата
docker-compose run --rm certbot certonly --webroot \
  --webroot-path=/var/www/certbot \
  $staging_arg \
  --email $email \
  --agree-tos \
  --no-eff-email \
  $domain_args

echo "### Перезапуск и обновление всех контейнеров..."
docker-compose down
docker-compose up -d

echo "### Готово! Сертификаты успешно получены."