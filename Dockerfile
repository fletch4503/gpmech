# Используем официальный образ Python
FROM python:3.13-slim

# Устанавливаем системные зависимости для PostgreSQL
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY pyproject.toml uv.lock ./

# Устанавливаем uv для управления зависимостями
RUN pip install uv

# Устанавливаем зависимости глобально (без виртуального окружения)
RUN uv pip install --system -r pyproject.toml

# Копируем исходный код
COPY . .

# Открываем порт 8501 для Streamlit
EXPOSE 8501

# Команда для запуска приложения
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]