<p align="center"><img src="https://github.com/exp-ext/upload/blob/main/backend/static/git/background.webp" width="700" /></p>


# Инструкция по развёртыванию проекта
## Описание
Проект представляет собой систему для загрузки и обработки изображений с использованием Django, Celery, Redis, и Postgres. Позволяет пользователям загружать изображения, которые затем асинхронно обрабатываются (преобразование формата, создание миниатюр) и сохраняются в облачное хранилище AWS S3.

## Технологии
- Django
- Docker
- Celery
- Redis
- PostgreSQL
- AWS S3

## Установка и запуск
### Требования
Для работы проекта необходимо установить Docker и Docker Compose.

### Запуск проекта
Клонируйте репозиторий:
```bash
git clone https://github.com/exp-ext/upload.git
```
Создайте файл .env в корне проекта и заполните его необходимыми переменными окружения:
```makefile
DEBUG=1
DJANGO_SECRET_KEY='ваш_секретный_ключ'
DJANGO_ALLOWED_HOSTS='localhost'
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD='пароль_redis'
USE_S3=1
AWS_S3_USE_SSL=1
AWS_ACCESS_KEY_ID='ваш_access_key_id'
AWS_SECRET_ACCESS_KEY='ваш_secret_access_key'
AWS_S3_ENDPOINT_URL='url_вашего_S3_хранилища'
AWS_S3_REGION_NAME='регион_S3_хранилища'
```
### Запустите Docker Compose для сборки и запуска контейнеров:
```bash
docker-compose up --build
```
После успешного запуска контейнеров, проект будет доступен по адресу http://localhost.

## Использование
Пользователи могут загружать изображения через предоставленный интерфейс https://you_domen/upload/photo/
Загруженные изображения обрабатываются в фоновом режиме с использованием Celery и сохраняются в AWS S3.
Результаты доступны через API проекта.

## Основные функции
- Загрузка изображений пользователями.
- Асинхронная обработка изображений (преобразование в форматы webp и crop).
- Сохранение обработанных изображений в AWS S3.
- Просмотр загруженных и обработанных изображений.

## Разработка
### Модели:
- Image - модель для хранения информации об изображениях.
### API:
- GetImagesLoadMeta - получение метаданных для загрузки изображений.
- ImageAsUploaded - подтверждение загрузки и запуск обработки изображений.
### Frontend
- Фронтенд реализован с использованием JavaScript и позволяет загружать изображения, а также отображать превью загруженных изображений.

### Задачи Celery
create_full_set_images - обработка изображений и создание полного набора изображений (оригинал, webp, crop).
___
## Project author:
- Borokin Andrey

- GITHUB: [exp-ext](https://github.com/exp-ext)

- [![Join Telegram](https://img.shields.io/badge/My%20Telegram-Join-blue)](https://t.me/Borokin)