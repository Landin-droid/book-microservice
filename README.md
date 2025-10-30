# Book Management Microservice

Микросервис для управления книгами с RESTful API, построенный на Flask, PostgreSQL и Docker.

## Технологии

- **Backend**: Flask, Python 3.9
- **Database**: PostgreSQL
- **Containerization**: Docker, Docker Compose
- **Logging**: Rotating File Handler
- **API Documentation**: Built-in error pages

## API Endpoints

| Метод | Endpoint | Описание | HTTP коды |
|-------|----------|----------|-----------|
| GET | `/health` | Проверка состояния сервиса | 200, 500 |
| GET | `/books` | Получить все книги | 200, 500 |
| POST | `/books` | Создать новую книгу | 201, 400, 409, 500 |
| GET | `/books/<id>` | Получить книгу по ID | 200, 404, 500 |
| PUT | `/books/<id>` | Обновить книгу | 200, 400, 404, 409, 500 |
| DELETE | `/books/<id>` | Удалить книгу | 200, 404, 500 |

## Установка и запуск

### Требования
- Docker
- Docker Compose

### Запуск проекта
```bash
# Клонирование репозитория
git clone https://github.com/Landin-droid/book-microservice.git
cd book-microservice

# Запуск сервисов
docker-compose up --build -d

# Проверка работы
curl http://localhost:5000/health
