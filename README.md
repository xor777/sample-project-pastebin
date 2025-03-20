# Pastebin

Простое приложение для хранения и обмена текстовыми сниппетами.

## Возможности

- Создание сниппетов с получением короткого URL
- Просмотр по уникальному URL
- Список всех сниппетов
- API для работы с сниппетами

## Установка

1. Клонируйте репозиторий

2. Создайте виртуальное окружение и установите зависимости:
   ```
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Настройте .env файл:
   ```
   cp .env.example .env
   ```

4. Инициализируйте базу данных:
   ```
   python db_manage.py init
   ```

## Запуск

```
python app.py
```

## API

### Создание сниппета
```bash
curl -X POST http://localhost:5001/create -H "Content-Type: application/json" -d '{"content":"Привет, мир!"}'
```

### Получение сниппета
```bash
curl http://localhost:5001/p/abC123
```

### Удаление сниппета
```bash
curl -X DELETE http://localhost:5001/p/abC123
```

### Список сниппетов
```bash
curl http://localhost:5001/list
``` 