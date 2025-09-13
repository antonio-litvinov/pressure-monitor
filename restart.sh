#!/bin/bash

echo "$(date): Останавливаем контейнеры..."

# Останавливаем контейнеры
docker compose down gigadoc
docker compose down ws_adapter

# Ждем 5 секунд для полной остановки
sleep 5

# Запускаем заново
echo "Запускаем контейнеры..."
docker compose up gigadoc -d
docker compose up ws_adapter -d

echo "$(date): Контейнеры запущены успешно"