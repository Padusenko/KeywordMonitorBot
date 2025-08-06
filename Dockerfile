# Використовуємо офіційний легкий образ Python
FROM python:3.11-slim

# Встановлюємо робочу директорію всередині контейнера
WORKDIR /app

# Копіюємо файл з вимогами і встановлюємо бібліотеки
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо весь інший код проекту в робочу директорію
COPY . .

# Команда запуску. Спочатку копіюємо сесію, потім запускаємо бота.
# "|| true" потрібно, щоб команда не завершилася з помилкою, якщо файл вже існує.
CMD cp /app/keyword_monitor_session /data/keyword_monitor_session || true; python main.py