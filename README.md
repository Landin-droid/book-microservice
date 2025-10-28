# Book Management Microservice

RESTful API для управления книгами в библиотеке.

## API Endpoints

- `GET /books` - Получить все книги
- `GET /books/<id>` - Получить книгу по ID  
- `POST /books` - Создать новую книгу
- `PUT /books/<id>` - Обновить книгу
- `DELETE /books/<id>` - Удалить книгу

## Запуск проекта

```bash
# Запуск через Docker Compose
docker-compose up --build

# Запуск в фоновом режиме
docker-compose up --build -d
