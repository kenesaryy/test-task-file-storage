# Django File Storage Service

Сервис для хранения файлов с автоматическим разбиением на 16 частей и архивацией.

## Структура проекта

```
project/
├── manage.py
├── project/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── file_storage/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── services.py
│   ├── views.py
│   ├── urls.py
│   └── migrations/
│       └── __init__.py
├── media/
│   └── file_parts/
├── requirements.txt
└── README.md
```

## Установка и запуск

1. Создайте виртуальное окружение:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # или
   venv\Scripts\activate  # Windows
   ```

2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

3. Выполните миграции:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. Создайте суперпользователя:
   ```bash
   python manage.py createsuperuser
   ```

5. Запустите сервер:
   ```bash
   python manage.py runserver
   ```

## API Endpoints

### Аутентификация
- POST `/admin/` - вход в админ-панель
- GET `/api-auth/login/` - страница входа для получения токена

### Работа с файлами
- POST `/api/storage/upload/` - загрузка файла
- GET `/api/storage/download/{file_id}/` - скачивание файла
- GET `/api/storage/files/` - список файлов пользователя
- DELETE `/api/storage/delete/{file_id}/` - удаление файла
- GET `/api/storage/logs/` - просмотр логов действий

## Примеры использования

### Получение токена аутентификации
```bash
# Через браузер перейдите на http://localhost:8000/api-auth/login/
# Войдите в систему и получите токен через админ-панель
```

### Загрузка файла
```bash
curl -X POST \
  -H "Authorization: Token YOUR_AUTH_TOKEN" \
  -F "file=@path/to/your/file.txt" \
  http://localhost:8000/api/storage/upload/
```

### Скачивание файла
```bash
curl -H "Authorization: Token YOUR_AUTH_TOKEN" \
  http://localhost:8000/api/storage/download/FILE_UUID/ \
  -o downloaded_file.txt
```

### Просмотр списка файлов
```bash
curl -H "Authorization: Token YOUR_AUTH_TOKEN" \
  http://localhost:8000/api/storage/files/
```

### Просмотр логов
```bash
curl -H "Authorization: Token YOUR_AUTH_TOKEN" \
  http://localhost:8000/api/storage/logs/
```

## Особенности

- Максимальный размер файла: 16MB
- Файлы автоматически разбиваются на 16 частей
- Каждая часть архивируется отдельно
- Проверка целостности через SHA256
- Полное логирование всех действий
- Использование UUID для идентификаторов