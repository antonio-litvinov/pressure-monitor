# 🚀 Руководство по развертыванию API сервера для записи видео

## 📋 Обзор

Данное руководство описывает пошаговую настройку API сервера для записи и обработки видео с использованием:
- **Python Flask** - API сервер
- **Nginx** - веб-сервер и прокси
- **Let's Encrypt** - SSL сертификаты
- **CORS** - для кросс-доменных запросов

## 🎯 Результат

После выполнения всех шагов у вас будет:
- ✅ API сервер на отдельном домене
- ✅ HTTPS с автоматическим обновлением сертификатов
- ✅ CORS настроен для основного сайта
- ✅ Видео сохраняется на сервере
- ✅ Работает на всех устройствах и браузерах

---

## 🔧 Шаг 1: Подготовка сервера

### Подключение к серверу
```bash
ssh username@your-server-ip
```

### Обновление системы
```bash
sudo apt update && sudo apt upgrade -y
```

### Установка необходимых пакетов
```bash
sudo apt install python3 python3-pip nginx certbot python3-certbot-nginx -y
```

---

## 📁 Шаг 2: Создание проекта

### Создание структуры проекта
```bash
mkdir tonometr && cd tonometr
```

### Создание файла зависимостей
```bash
cat > requirements.txt << 'EOF'
Flask==3.0.0
Werkzeug==3.0.1
EOF
```

### Установка зависимостей
```bash
pip3 install -r requirements.txt
```

---

## 🐍 Шаг 3: Создание Python сервера

### Создание файла сервера
---

## 🌐 Шаг 4: Настройка Nginx

### Создание конфигурации Nginx
```bash
sudo nano /etc/nginx/sites-available/tonometr
```

### Базовая конфигурация (вставить в файл)
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Активация сайта
```bash
# Создать символическую ссылку
sudo ln -s /etc/nginx/sites-available/tonometr /etc/nginx/sites-enabled/

# Удалить дефолтный сайт
sudo rm /etc/nginx/sites-enabled/default

# Проверить конфигурацию
sudo nginx -t

# Запустить Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

---

## 🌍 Шаг 5: Настройка DNS

В панели управления доменом добавить A-запись:
```
A    api.yourdomain.com    →    your-server-ip
```

**Пример:**
```
A    api.pressure-monitor.ru    →    195.209.214.181
```

---

## 🔐 Шаг 6: Получение SSL сертификата

### Получение сертификата Let's Encrypt
```bash
sudo certbot --nginx -d api.yourdomain.com
```

### При установке certbot спросит:
- **Email** - введите ваш email для уведомлений
- **Terms of Service** - нажмите `Y` для принятия
- **Newsletter** - по желанию (рекомендуется `N`)
- **Redirect** - выберите **2** (redirect all traffic to HTTPS)

---

## 🚦 Шаг 7: Настройка CORS в Nginx

### Обновление конфигурации Nginx
```bash
sudo nano /etc/nginx/sites-available/tonometr
```

### Полная конфигурация с CORS (заменить содержимое)
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Увеличиваем лимит размера файла
    client_max_body_size 100M;
    
    # Обработка OPTIONS запросов (preflight)
    location = /api/process-video {
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' 'https://yourdomain.com' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
            add_header 'Access-Control-Allow-Headers' 'Content-Type,Authorization' always;
            add_header 'Access-Control-Max-Age' 1728000 always;
            add_header 'Content-Type' 'text/plain; charset=utf-8' always;
            add_header 'Content-Length' 0 always;
            return 204;
        }
        
        # CORS заголовки для POST запросов
        add_header 'Access-Control-Allow-Origin' 'https://yourdomain.com' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'Content-Type,Authorization' always;
        
        # Увеличиваем таймауты для больших файлов
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Общий location для остальных запросов
    location / {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**⚠️ Важно:** Замените `yourdomain.com` на ваш реальный домен!

### Перезапуск Nginx
```bash
# Проверить конфигурацию
sudo nginx -t

# Если все OK, перезапустить
sudo systemctl reload nginx

# Проверить статус
sudo systemctl status nginx
```

---

## 🔥 Шаг 8: Настройка файрвола

### Открытие необходимых портов
```bash
# Открыть порты
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS

# Включить файрвол
sudo ufw enable

# Проверить статус
sudo ufw status
```

---

## 🚀 Шаг 9: Запуск Python сервера

### Создание screen сессии
```bash
# Установить screen (если не установлен)
sudo apt install screen

# Создать screen сессию
screen -S tonometr

# Запустить сервер
python3 video_server.py

# Отключиться от screen: Ctrl+A, затем D
```

### Альтернативный способ (nohup)
```bash
nohup python3 video_server.py > server.log 2>&1 &
```

---

## 📱 Шаг 10: Обновление HTML

В HTML файле на основном сайте обновить конфигурацию:

```javascript
// Старая конфигурация
const SERVER_CONFIG = {
    baseUrl: 'http://195.209.214.181:5002',
    endpoints: {
        processVideo: '/api/process-video'
    }
};

// Новая конфигурация
const SERVER_CONFIG = {
    baseUrl: 'https://api.yourdomain.com',
    endpoints: {
        processVideo: '/api/process-video'
    }
};
```

---

## 🧪 Тестирование

### Проверка работы сервера
```bash
# Проверить статус Nginx
sudo systemctl status nginx

# Проверить порты
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443

# Проверить Python процесс
ps aux | grep python3
```

### Тест API endpoint
```bash
# Тест с локальной машины
curl https://api.yourdomain.com/api/process-video
# Должна вернуться 405 ошибка (это нормально для GET запроса)
```

### Тест загрузки видео
1. Откройте основной сайт в браузере
2. Запишите видео (10 секунд)
3. Проверьте консоль браузера на ошибки
4. Проверьте папку `videos/` на сервере

---

## 🔧 Устранение неполадок

### Проблема: 502 Bad Gateway
```bash
# Проверить, запущен ли Python сервер
ps aux | grep python3

# Если не запущен, запустить
screen -r tonometr
# или
python3 video_server.py
```

### Проблема: CORS ошибки
```bash
# Проверить конфигурацию Nginx
sudo nginx -t

# Перезапустить Nginx
sudo systemctl reload nginx
```

### Проблема: SSL сертификат не работает
```bash
# Проверить статус certbot
sudo certbot certificates

# Обновить сертификат
sudo certbot renew
```

---

## 📊 Мониторинг

### Просмотр логов
```bash
# Логи Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Логи Python сервера (если используете nohup)
tail -f server.log

# Логи Python сервера (если используете screen)
screen -r tonometr
```

### Автоматическое обновление SSL
```bash
# Проверить cron задачи
sudo crontab -l

# Вручную обновить сертификат
sudo certbot renew
```

---

## 🎯 Время выполнения

- **Подготовка сервера:** 10-15 минут
- **Настройка Nginx:** 5 минут
- **SSL сертификат:** 2-3 минуты
- **CORS настройка:** 5 минут
- **Тестирование:** 5 минут

**Итого: ~30 минут** для полной настройки

---

## ✅ Чек-лист готовности

- [ ] Сервер обновлен и пакеты установлены
- [ ] Python сервер создан и работает
- [ ] Nginx настроен и запущен
- [ ] DNS записи добавлены
- [ ] SSL сертификат получен
- [ ] CORS настроен правильно
- [ ] Файрвол настроен
- [ ] Python сервер запущен в фоне
- [ ] HTML обновлен с новым API адресом
- [ ] Видео загружается без ошибок

---

## 🆘 Поддержка

При возникновении проблем:
1. Проверьте логи Nginx: `/var/log/nginx/error.log`
2. Проверьте логи Python сервера
3. Убедитесь, что все порты открыты
4. Проверьте DNS настройки
5. Убедитесь, что SSL сертификат действителен

---

## 📝 Примечания

- **Python сервер** должен быть запущен постоянно
- **SSL сертификат** обновляется автоматически каждые 60 дней
- **CORS настройки** специфичны для вашего основного домена
- **Размер файлов** ограничен 100 МБ (можно изменить в конфигурации)

---

*Последнее обновление: Август 2025*
