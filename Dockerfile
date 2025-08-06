# Використовуємо офіційний легкий образ Python
FROM python:3.11-slim

# Встановлюємо робочу директорію всередині контейнера
WORKDIR /app

# Копіюємо файл з вимогами і встановлюємо бібліотеки
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо весь інший код проекту в робочу директорію
COPY . .

# Створюємо скрипт запуску, який спочатку копіює сесію, а потім запускає бота
# Цей скрипт виконається ТІЛЬКИ ОДИН РАЗ при першому запуску контейнера
RUN echo '#!/bin/sh' > /app/start.sh && \
    echo 'if [ -f /app/keyword_monitor_session ] && [ ! -f /data/keyword_monitor_session ]; then cp /app/keyword_monitor_session /data/; echo "Session file copied to persistent storage."; fi' >> /app/start.sh && \
    echo 'exec python main.py' >> /app/start.sh && \
    chmod +x /app/start.sh

# Вказуємо наш новий скрипт як команду для запуску
CMD ["/app/start.sh"]