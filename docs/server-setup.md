# Настройка сервера

Пошаговая инструкция по подготовке чистого Ubuntu-сервера для продакшен-развёртывания pressure-monitor: пользователь и SSH, Docker, домен с HTTPS, базовая защита и автоперезапуск.

## Пользователь и SSH-доступ

```bash
adduser antonio
sudo passwd antonio
usermod -aG sudo antonio
```

### Если вы под root

```bash
mkdir -p /home/antonio/.ssh
chmod 700 /home/antonio/.ssh
chown antonio:antonio /home/antonio/.ssh
chmod 600 /home/antonio/.ssh/authorized_keys
chown antonio:antonio /home/antonio/.ssh/authorized_keys
```

### Если вы уже под antonio

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
nano ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

Если публичный ключ уже есть на локальной машине:

```bash
ssh-copy-id -i ~/.ssh/id_ed25519.pub antonio@<ip>
```

### Авторизация только по ключу

```bash
sudoedit /etc/ssh/sshd_config
```

Изменить/добавить:

```
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
PermitRootLogin no
MaxAuthTries 3
AllowUsers antonio
```

```bash
sudo sshd -t    # проверка конфига
sudo systemctl reload ssh
```

## Установка Docker

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

## Запуск контейнеров

### AI-модель (gigadoc)

1. Загрузить образ из архива: `docker load -i ws_gigadoc_cpu.tar.gz`
2. Скопировать папку `ws_adapter` на сервер
3. `docker compose build`
4. `docker compose up -d`

### Сборка сервисов вручную (без compose)

```bash
docker build -t image-name .
docker run -d -p 5000:5000 --env-file .env --name container-name image-name
docker run -e GIGADOC_TOKEN="ваш_токен" image-name
```

### Telegram-бот

```bash
docker build -t telegram_bot .
docker run -d --name telegram_bot --restart unless-stopped --env-file .env telegram_bot
```

## Домен и HTTPS

### Установка пакетов

```bash
sudo apt install nginx certbot python3-certbot-nginx -y
```

### Конфигурация Nginx

```bash
sudo nano /etc/nginx/sites-available/gigadoc
```

Базовая конфигурация (см. также [`nginx.conf`](../nginx.conf) в корне репозитория):

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
sudo ln -s /etc/nginx/sites-available/gigadoc /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl start nginx
sudo systemctl enable nginx
```

### Сертификат Let's Encrypt

```bash
sudo certbot --nginx -d api.pressure-monitor.ru
```

### Перезапуск после изменений

```bash
sudo nginx -t
sudo systemctl reload nginx
sudo systemctl status nginx
```

## Защита сервера

### Лог аутентификаций

```bash
sudo cat /var/log/auth.log | grep "Failed password"
```

### Firewall (ufw)

```bash
sudo lsof -i -P -n | grep LISTEN   # открытые порты

sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS

sudo ufw default deny incoming
sudo ufw default allow outgoing

sudo ufw enable
sudo ufw status
```

### fail2ban

```bash
sudo apt install fail2ban
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
```

В `/etc/fail2ban/jail.local`:

```ini
[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 5
bantime.increment = true
bantime.factor = 2
bantime.rndtime = 10m

[sshd]
enabled = true

[nginx-http-auth]
enabled = true

[nginx-badbots]
enabled = true
```

```bash
sudo systemctl restart fail2ban
sudo fail2ban-client status sshd
```

## Запуск без Docker (screen / nohup)

```bash
sudo apt install screen
screen -S tonometr
python3 video_server.py
# отключиться: Ctrl+A, затем D
# вернуться:    screen -r tonometr
```

Или через `nohup`:

```bash
nohup python3 video_server.py > server.log 2>&1 &
tail -f server.log
```

## Проверка и логи

```bash
sudo systemctl status nginx
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443
ps aux | grep python3

sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## Автоперезапуск через cron

`ws_adapter` и `gigadoc` иногда требуют планового рестарта — для этого в репозитории есть [`restart.sh`](../restart.sh).

```bash
crontab -e
```

Каждый час в 0 минут:

```
0 * * * * /home/antonio/restart.sh >> /home/antonio/ws-adapter-restart.log 2>&1
```

Каждые полчаса:

```
*/30 * * * * /home/antonio/restart.sh >> /home/antonio/ws-adapter-restart.log 2>&1
```

Проверка:

```bash
crontab -l
tail -f /home/antonio/ws-adapter-restart.log
```

## Полезные команды Docker

```bash
docker ps            # запущенные контейнеры
docker ps -a          # все контейнеры, включая остановленные

docker system prune -a --volumes   # быстрая очистка всего неиспользуемого

docker stop $(docker ps -aq)
docker rm $(docker ps -aq)
docker rmi $(docker images -aq)
docker volume prune -f
docker network prune -f
docker builder prune -a -f
```
