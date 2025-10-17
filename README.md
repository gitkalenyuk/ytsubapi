# YouTube Subtitles API

API для отримання субтитрів з YouTube відео за допомогою pytubefix.

## Функціональність
- Отримання субтитрів з YouTube відео
- Підтримка різних мов
- Автоматичне очищення тексту від тайм-кодів
- Інформація про відео та доступні субтитри

## Endpoints
### GET /subtitles
Отримує субтитри з YouTube відео.
**Параметри:**
- `url` (обов'язковий) - YouTube URL відео
- `lang` (опціональний, за замовчуванням "en") - мова субтитрів
**Приклад запиту:**
GET /subtitles?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&lang=en
**Відповідь:** Plain text з субтитрами

### GET /subtitles/info
Отримує інформацію про відео та доступні субтитри.
**Параметри:**
- `url` (обов'язковий) - YouTube URL відео
**Приклад запиту:**
GET /subtitles/info?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ
**Відповідь:** JSON з відео та субтитрами

### GET /health
Перевірка стану API

## Локальна розробка
pip install -r requirements.txt
python main.py

## Розгортання на Vercel
1. Завантажте файли у GitHub
2. Під'єднайте репозиторій до Vercel
3. Натисніть Deploy
