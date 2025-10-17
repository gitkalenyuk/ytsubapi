# Створюємо структуру проекту для Vercel
import os

# Створюємо основні файли проекту

# 1. main.py - основний API файл
main_py_content = """from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import re
from pytubefix import YouTube
import logging

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="YouTube Subtitles API",
    description="API для отримання субтитрів з YouTube відео",
    version="1.0.0"
)

# Додаємо CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_video_id(url: str) -> str:
    \"\"\"Витягує ID відео з YouTube URL\"\"\"
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        r'youtube\.com\/watch\?.*v=([^&\n?#]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    raise ValueError("Неправильний YouTube URL")

@app.get("/")
async def root():
    return {
        "message": "YouTube Subtitles API", 
        "version": "1.0.0",
        "endpoints": {
            "/subtitles": "GET - отримання субтитрів",
            "/health": "GET - перевірка стану API"
        }
    }

@app.get("/health")
async def health():
    return {"status": "ok", "message": "API працює нормально"}

@app.get("/subtitles", response_class=PlainTextResponse)
async def get_subtitles(
    url: str = Query(..., description="YouTube URL відео"),
    lang: str = Query("en", description="Мова субтитрів (en, uk, it, auto тощо)")
):
    \"\"\"
    Отримує субтитри з YouTube відео
    
    Args:
        url: YouTube URL
        lang: Мова субтитрів (за замовчуванням 'en')
    
    Returns:
        Текст субтитрів у plain text форматі
    \"\"\"
    try:
        logger.info(f"Отримання субтитрів для URL: {url}, мова: {lang}")
        
        # Витягуємо ID відео
        video_id = extract_video_id(url)
        logger.info(f"Video ID: {video_id}")
        
        # Створюємо YouTube об'єкт
        yt = YouTube(url)
        
        # Отримуємо список доступних субтитрів
        captions = yt.captions
        
        if not captions:
            raise HTTPException(status_code=404, detail="Субтитри недоступні для цього відео")
        
        # Шукаємо субтитри потрібною мовою
        caption = None
        
        # Спочатку шукаємо точну мову
        if lang in captions:
            caption = captions[lang]
        # Якщо не знайдено, шукаємо автосубтитри
        elif f"a.{lang}" in captions:
            caption = captions[f"a.{lang}"]
        # Якщо lang="auto", берем перші доступні
        elif lang == "auto" and captions:
            caption = list(captions.values())[0]
        # Fallback на англійську
        elif "en" in captions:
            caption = captions["en"]
        elif "a.en" in captions:
            caption = captions["a.en"]
        
        if not caption:
            available_langs = list(captions.keys())
            raise HTTPException(
                status_code=404, 
                detail=f"Субтитри мовою '{lang}' не знайдено. Доступні мови: {available_langs}"
            )
        
        # Отримуємо текст субтитрів
        subtitle_text = caption.generate_srt_captions()
        
        logger.info("Субтитри успішно отримано")
        
        # Очищуємо текст від тайм-кодів (залишаємо тільки текст)
        lines = subtitle_text.split('\\n')
        clean_text = []
        
        for line in lines:
            line = line.strip()
            # Пропускаємо номери, тайм-коди та пусті рядки
            if (line and 
                not line.isdigit() and 
                not '-->' in line and 
                not re.match(r'^\\d+$', line)):
                clean_text.append(line)
        
        result = ' '.join(clean_text)
        
        if not result.strip():
            raise HTTPException(status_code=404, detail="Не вдалося отримати текст субтитрів")
        
        return result
        
    except ValueError as e:
        logger.error(f"Помилка URL: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Помилка отримання субтитрів: {e}")
        raise HTTPException(status_code=500, detail=f"Помилка сервера: {str(e)}")

@app.get("/subtitles/info")
async def get_video_info(url: str = Query(..., description="YouTube URL відео")):
    \"\"\"
    Отримує інформацію про відео та доступні субтитри
    \"\"\"
    try:
        video_id = extract_video_id(url)
        yt = YouTube(url)
        
        # Інформація про відео
        video_info = {
            "title": yt.title,
            "author": yt.author,
            "length": yt.length,
            "views": yt.views,
            "video_id": video_id,
            "thumbnail": yt.thumbnail_url
        }
        
        # Доступні субтитри
        captions_info = {}
        for lang_code, caption in yt.captions.items():
            captions_info[lang_code] = {
                "language": caption.name,
                "code": caption.code,
                "auto_generated": caption.code.startswith('a.')
            }
        
        return {
            "video": video_info,
            "available_captions": captions_info
        }
        
    except Exception as e:
        logger.error(f"Помилка отримання інформації: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""

# 2. requirements.txt - залежності
requirements_txt = """fastapi>=0.104.1
uvicorn[standard]>=0.24.0
pytubefix>=10.0.0
python-multipart>=0.0.6
"""

# 3. vercel.json - конфігурація для Vercel
vercel_json = """{
  "version": 2,
  "builds": [
    {
      "src": "main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "main.py"
    }
  ]
}"""

# 4. README.md - документація
readme_md = """# YouTube Subtitles API

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
```
GET /subtitles?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&lang=en
```

**Відповідь:** Plain text з субтитрами

### GET /subtitles/info

Отримує інформацію про відео та доступні субтитри.

**Параметри:**
- `url` (обов'язковий) - YouTube URL відео

**Приклад запиту:**
```
GET /subtitles/info?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

**Відповідь:** JSON з інформацією про відео та субтитри

### GET /health

Перевірка стану API.

## Підтримувані мови

API підтримує будь-які мови, доступні для конкретного відео:
- `en` - англійська
- `uk` - українська  
- `it` - італійська
- `auto` - автоматичний вибір першої доступної мови
- Інші мови за ISO кодами

## Локальна розробка

1. Встановіть залежності:
```bash
pip install -r requirements.txt
```

2. Запустіть сервер:
```bash
python main.py
```

API буде доступне на http://localhost:8000

## Розгортання на Vercel

1. Завантажте всі файли до GitHub репозиторію
2. Підключіть репозиторій до Vercel
3. Vercel автоматично розгорне API

## Використання

Після розгортання ваш API буде доступний за адресою типу:
`https://your-project-name.vercel.app/subtitles?url=YOUTUBE_URL`
"""

# 5. .gitignore
gitignore = """__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

.vercel
"""

# Створюємо файли
files_content = {
    "main.py": main_py_content,
    "requirements.txt": requirements_txt,
    "vercel.json": vercel_json,
    "README.md": readme_md,
    ".gitignore": gitignore
}

print("Створено файли проекту:")
for filename, content in files_content.items():
    print(f"\n📄 {filename}")
    print("=" * 50)
    print(content[:200] + "..." if len(content) > 200 else content)

print(f"\n✅ Всього створено {len(files_content)} файлів для проекту YouTube Subtitles API")