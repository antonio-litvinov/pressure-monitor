### Настройка сервера

```bash
adduser antonio
sudo passwd antonio
usermod -aG sudo antonio
```

#### Если под root:
```bash
mkdir -p /home/antonio/.ssh
chmod 700 /home/antonio/.ssh
chown antonio:antonio /home/antonio/.ssh
chmod 600 /home/antonio/.ssh/authorized_keys
chown antonio:antonio /home/antonio/.ssh/authorized_keys
```

#### Если под antonio:
```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
nano ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

Если уже есть публичный ключ на локальной машине, то:
ssh-copy-id -i ~/.ssh/id_ed25519.pub antonio@<ip>

#### Настройка авторизации на сервере:

```bash
sudoedit /etc/ssh/sshd_config
```

#### поменять/добавить:
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
PermitRootLogin no
MaxAuthTries 3
AllowUsers antonio

```bash
sudo sshd -t    # проверка конфига
sudo systemctl reload ssh
```

# Или посмотреть весь лог аутентификаций
```bash
sudo cat /var/log/auth.log | grep "Failed password"
```


docker build -t video_server .

docker run -d -p 5000:5000 --env-file .env --name test video_server


   docker run -e GIGADOC_TOKEN="ваш_токен" your-image

   environment:
     - GIGADOC_TOKEN=ваш_токен



### Установка Docker
```bash
sudo apt update 
sudo apt install apt-transport-https ca-certificates curl software-properties-common 

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"

sudo apt update 
sudo apt install docker-ce
sudo systemctl status docker

sudo usermod -aG docker $USER
```

### Запуск docker образа

1. Загрузить скаченный образ из архива командой `docker load -i ws_gigadoc_cpu.tar.gz`
2. Скопировать папку ws_adapter на сервер
3. Запустить `docker compose build`
4. Поднять контейнеры `docker compose up -d`

### Установка необходимых пакетов
```bash
sudo apt install nginx certbot python3-certbot-nginx -y
```

### Создание конфигурации Nginx
```bash
sudo nano /etc/nginx/sites-available/gigadoc
```

### Базовая конфигурация (вставить в файл)
```nginx
server {
    listen 80;
    server_name api.pressure-monitor.ru;

    location / {
        proxy_pass http://127.0.0.1:5000;
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
sudo ln -s /etc/nginx/sites-available/gigadoc /etc/nginx/sites-enabled/

# Удалить дефолтный сайт
sudo rm /etc/nginx/sites-enabled/default

# Проверить конфигурацию
sudo nginx -t

# Запустить Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### Получение сертификата Let's Encrypt
```bash
sudo certbot --nginx -d api.pressure-monitor.ru
```

### Внести изменения из nginx.conf
sudo rm /etc/nginx/sites-available/gigadoc
sudo nano /etc/nginx/sites-available/gigadoc

### Перезапуск Nginx
```bash
# Проверить конфигурацию
sudo nginx -t

# Если все OK, перезапустить
sudo systemctl reload nginx

# Проверить статус
sudo systemctl status nginx
```

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

### Настройка CRON

#### Откройте crontab для редактирования:
```bash
crontab -e
```

#### Перезапуск каждый час в 0 минут:
```bash
0 * * * * /path/to/your/ws_adapter/restart.sh >> /var/log/ws-adapter-restart.log 2>&1
```

#### Перезапуск каждые полчаса:
```bash
*/30 * * * * /path/to/your/ws_adapter/restart.sh >> /var/log/ws-adapter-restart.log 2>&1
```

#### Проверьте, что cron работает:
```bash
# Проверить активные cron задачи
crontab -l

# Проверить логи cron
sudo tail -f /var/log/cron

# Проверить логи перезапуска
tail -f /var/log/ws-adapter-restart.log
```