from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import re
from pytubefix import YouTube
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="YouTube Subtitles API",
    description="API для отримання субтитрів з YouTube відео",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_video_id(url: str) -> str:
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
    try:
        logger.info(f"Отримання субтитрів для URL: {url}, мова: {lang}")
        video_id = extract_video_id(url)
        logger.info(f"Video ID: {video_id}")
        yt = YouTube(url, use_po_token=True)
        captions = yt.captions
        if not captions:
            raise HTTPException(status_code=404, detail="Субтитри недоступні для цього відео")
        caption = None
        if lang in captions:
            caption = captions[lang]
        elif f"a.{lang}" in captions:
            caption = captions[f"a.{lang}"]
        elif lang == "auto" and captions:
            caption = list(captions.values())[0]
        elif "en" in captions:
            caption = captions["en"]
        elif "a.en" in captions:
            caption = captions["a.en"]
        if not caption:
            available_langs = list(captions.keys())
            raise HTTPException(status_code=404, detail=f"Субтитри мовою '{lang}' не знайдено. Доступні мови: {available_langs}")
        subtitle_text = caption.generate_srt_captions()
        logger.info("Субтитри успішно отримано")
        lines = subtitle_text.split('\n')
        clean_text = []
        for line in lines:
            line = line.strip()
            if (line and not line.isdigit() and not '-->' in line and not re.match(r'^\d+$', line)):
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
    try:
        video_id = extract_video_id(url)
        yt = YouTube(url, use_po_token=True)
        video_info = {
            "title": yt.title,
            "author": yt.author,
            "length": yt.length,
            "views": yt.views,
            "video_id": video_id,
            "thumbnail": yt.thumbnail_url
        }
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
