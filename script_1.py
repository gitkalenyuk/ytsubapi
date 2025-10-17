# Виправляємо regex та створюємо CSV файли для завантаження
import csv
import io

# Створюємо кожен файл окремо для завантаження
files_to_create = {}

# 1. main.py - виправлений код
main_py_fixed = '''from fastapi import FastAPI, HTTPException, Query
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
    """Витягує ID відео з YouTube URL"""
    patterns = [
        r'(?:youtube\\.com\\/watch\\?v=|youtu\\.be\\/|youtube\\.com\\/embed\\/)([^&\\n?#]+)',
        r'youtube\\.com\\/watch\\?.*v=([^&\\n?#]+)'
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
    """
    Отримує субтитри з YouTube відео
    
    Args:
        url: YouTube URL
        lang: Мова субтитрів (за замовчуванням 'en')
    
    Returns:
        Текст субтитрів у plain text форматі
    """
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
    """
    Отримує інформацію про відео та доступні субтитри
    """
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
'''

# Записуємо всі файли як CSV для завантаження
files_data = [
    ["filename", "content"],
    ["main.py", main_py_fixed],
    ["requirements.txt", "fastapi>=0.104.1\nuvicorn[standard]>=0.24.0\npytubefix>=10.0.0\npython-multipart>=0.0.6"],
    ["vercel.json", '{\n  "version": 2,\n  "builds": [\n    {\n      "src": "main.py",\n      "use": "@vercel/python"\n    }\n  ],\n  "routes": [\n    {\n      "src": "/(.*)",\n      "dest": "main.py"\n    }\n  ]\n}'],
    ["README.md", "# YouTube Subtitles API\n\nAPI для отримання субтитрів з YouTube відео за допомогою pytubefix.\n\n## Функціональність\n\n- Отримання субтитрів з YouTube відео\n- Підтримка різних мов\n- Автоматичне очищення тексту від тайм-кодів\n- Інформація про відео та доступні субтитри\n\n## Endpoints\n\n### GET /subtitles\n\nОтримує субтитри з YouTube відео.\n\n**Параметри:**\n- `url` (обов'язковий) - YouTube URL відео\n- `lang` (опціональний, за замовчуванням \"en\") - мова субтитрів\n\n**Приклад запиту:**\n```\nGET /subtitles?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&lang=en\n```\n\n**Відповідь:** Plain text з субтитрами"],
    [".gitignore", "__pycache__/\n*.py[cod]\n*$py.class\n*.so\n.Python\nbuild/\ndevelop-eggs/\ndist/\ndownloads/\neggs/\n.eggs/\nlib/\nlib64/\nparts/\nsdist/\nvar/\nwheels/\n*.egg-info/\n.installed.cfg\n*.egg\nMANIFEST\n\n.env\n.venv\nenv/\nvenv/\nENV/\nenv.bak/\nvenv.bak/\n\n.vercel"]
]

# Створюємо CSV файл з усіма файлами проекту
output = io.StringIO()
writer = csv.writer(output)
writer.writerows(files_data)
csv_content = output.getvalue()

# Зберігаємо в файл
with open('youtube_api_project_files.csv', 'w', encoding='utf-8', newline='') as f:
    f.write(csv_content)

print("✅ Проект готовий! Створено файл 'youtube_api_project_files.csv' з усіма необхідними файлами.")
print("\n📋 Інструкція по розгортанню:")
print("1. Створи новий GitHub репозиторій")
print("2. Завантаж усі файли з CSV до репозиторію")
print("3. У Vercel натисни 'Import Project' і вибери свій репозиторій")
print("4. Vercel автоматично розгорне API")
print("\n🔗 Після розгортання твій API буде доступний за адресою:")
print("https://your-project-name.vercel.app/subtitles?url=YOUTUBE_URL&lang=uk")