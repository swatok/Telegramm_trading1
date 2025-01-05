# Розгортання системи

## Вимоги до системи

### Системні вимоги
- CPU: 2+ ядра
- RAM: 4+ GB
- Диск: 50+ GB SSD
- ОС: Ubuntu 20.04+ / Debian 10+

### Програмні залежності
- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Docker 20+
- Docker Compose 1.29+

### Мережеві вимоги
- Стабільне інтернет-з'єднання
- Відкриті порти:
  - 5432 (PostgreSQL)
  - 6379 (Redis)
  - 8080 (API)
  - 8081 (Метрики)

## Підготовка середовища

### Встановлення залежностей
```bash
# Оновлення системи
apt update && apt upgrade -y

# Встановлення базових пакетів
apt install -y python3.8 python3.8-venv python3-pip postgresql redis-server docker.io docker-compose

# Створення віртуального середовища
python3.8 -m venv venv
source venv/bin/activate

# Встановлення Python залежностей
pip install -r requirements.txt
```

### Налаштування PostgreSQL
```bash
# Створення бази даних та користувача
sudo -u postgres psql -c "CREATE DATABASE trading_bot;"
sudo -u postgres psql -c "CREATE USER trading_user WITH PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE trading_bot TO trading_user;"

# Налаштування доступу
echo "host all trading_user 0.0.0.0/0 md5" >> /etc/postgresql/12/main/pg_hba.conf
echo "listen_addresses = '*'" >> /etc/postgresql/12/main/postgresql.conf

# Перезапуск PostgreSQL
systemctl restart postgresql
```

### Налаштування Redis
```bash
# Налаштування конфігурації
sed -i 's/bind 127.0.0.1/bind 0.0.0.0/g' /etc/redis/redis.conf
sed -i 's/# requirepass foobared/requirepass redis_password/g' /etc/redis/redis.conf

# Перезапуск Redis
systemctl restart redis
```

## Розгортання додатку

### Використання Docker

#### Створення образів
```bash
# Збірка образів
docker-compose build

# Перевірка образів
docker images
```

#### Запуск контейнерів
```bash
# Запуск всіх сервісів
docker-compose up -d

# Перевірка статусу
docker-compose ps
```

#### Моніторинг логів
```bash
# Перегляд логів всіх контейнерів
docker-compose logs -f

# Перегляд логів конкретного сервісу
docker-compose logs -f trading-bot
```

### Ручне розгортання

#### Налаштування конфігурації
```bash
# Копіювання конфігурації
cp config.example.yaml config.yaml

# Редагування конфігурації
nano config.yaml
```

#### Запуск сервісів
```bash
# Запуск основного процесу
python main.py

# Запуск воркерів
python worker.py
```

#### Налаштування системного сервісу
```bash
# Створення systemd сервісу
cat > /etc/systemd/system/trading-bot.service << EOL
[Unit]
Description=Trading Bot Service
After=network.target

[Service]
Type=simple
User=trading
WorkingDirectory=/opt/trading-bot
ExecStart=/opt/trading-bot/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# Активація сервісу
systemctl enable trading-bot
systemctl start trading-bot
```

## Оновлення системи

### Оновлення через Docker
```bash
# Зупинка контейнерів
docker-compose down

# Оновлення образів
docker-compose pull

# Перезапуск контейнерів
docker-compose up -d
```

### Ручне оновлення
```bash
# Зупинка сервісу
systemctl stop trading-bot

# Оновлення коду
git pull origin master

# Оновлення залежностей
pip install -r requirements.txt

# Запуск міграцій
python manage.py migrate

# Перезапуск сервісу
systemctl start trading-bot
```

## Моніторинг та обслуговування

### Перевірка статусу
```bash
# Статус сервісу
systemctl status trading-bot

# Перевірка логів
journalctl -u trading-bot -f

# Перевірка метрик
curl http://localhost:8081/metrics
```

### Бекапи
```bash
# Бекап бази даних
pg_dump -U trading_user trading_bot > backup.sql

# Бекап конфігурації
cp config.yaml config.backup.yaml

# Бекап даних Redis
redis-cli -a redis_password save
```

### Відновлення
```bash
# Відновлення бази даних
psql -U trading_user trading_bot < backup.sql

# Відновлення конфігурації
cp config.backup.yaml config.yaml

# Перезапуск сервісів
systemctl restart trading-bot
```

## Безпека

### Налаштування файрволу
```bash
# Дозвіл необхідних портів
ufw allow 22/tcp
ufw allow 5432/tcp
ufw allow 6379/tcp
ufw allow 8080/tcp
ufw allow 8081/tcp

# Активація файрволу
ufw enable
```

### SSL/TLS
```bash
# Генерація сертифікатів
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/trading-bot.key \
  -out /etc/ssl/certs/trading-bot.crt

# Налаштування прав доступу
chmod 600 /etc/ssl/private/trading-bot.key
chmod 644 /etc/ssl/certs/trading-bot.crt
```

### Шифрування даних
```bash
# Генерація ключа шифрування
openssl rand -base64 32 > encryption.key

# Налаштування прав доступу
chmod 600 encryption.key
chown trading:trading encryption.key
```

## Усунення несправностей

### Перевірка логів
```bash
# Системні логи
tail -f /var/log/syslog

# Логи додатку
tail -f /var/log/trading-bot/app.log

# Логи бази даних
tail -f /var/log/postgresql/postgresql-12-main.log
```

### Діагностика проблем
```bash
# Перевірка використання ресурсів
top
htop
df -h
free -m

# Перевірка мережі
netstat -tulpn
ping api.mainnet-beta.solana.com
```

### Очищення даних
```bash
# Очищення старих логів
find /var/log/trading-bot -type f -name "*.log.*" -mtime +30 -delete

# Очищення тимчасових файлів
rm -rf /tmp/trading-bot/*

# Очищення кешу Redis
redis-cli -a redis_password FLUSHALL
``` 