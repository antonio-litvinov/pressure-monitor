#!/bin/bash

echo "$(date): Restarting ws-adapter..."

# Останавливаем контейнер
echo "Stopping containers..."
docker compose down

# Ждем 5 секунд для полной остановки
sleep 5

# Запускаем заново
echo "Starting containers..."
docker compose up -d

echo "$(date): ws-adapter restarted successfully"
echo "Container status:"
docker compose ps