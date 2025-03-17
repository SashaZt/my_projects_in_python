#!/bin/bash

# Проверяем доступность Nginx
if curl -s http://localhost/nginx-health > /dev/null; then
  echo "Nginx is healthy"
  exit 0
else
  echo "Nginx is not healthy"
  exit 1
fi