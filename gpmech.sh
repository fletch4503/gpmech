#!/bin/bash
# Interactive menu for common project commands

echo "Выберите команду для запуска:"
echo "1) Для первого запуска -> Установить виртуальное окружение, создание Docker-контейнера и запуск приложения"
echo "2) Остановить и удалить контейнер"
echo "3) Запуск проекта без установки зависимостей"
echo "4) Exit"

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo "Установливаем виртуальное окружение..."
        uv venv && uv sync
        echo "Создаем и запускаем контейнер в Docker..."
        docker-compose up -d postgres
        echo "Запускаем приложение..."
        uv run streamlit run main.py
        read -p "Press Enter to continue..."
        ;;
    2)
        echo "Stopping containers..."
        docker-compose down
        read -p "Press Enter to continue..."
        ;;
    3)
        echo "Создаем и запускаем контейнер в Docker..."
        docker-compose up --build -d postgres
        echo "Запускаем приложение..."
        uv run streamlit run main.py
        read -p "Press Enter to continue..."
        ;;
    4)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac
