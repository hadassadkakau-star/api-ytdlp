
import os
import uuid
import time
import glob
import shutil
import threading

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from yt_dlp import YoutubeDL

app = FastAPI(title="API YT-DLP")

DOWNLOAD_DIR = "/tmp/ytdlp"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

files = {}
lock = threading.Lock()


@app.get("/")
def home():
    return {
        "status": "online",
        "api": "YT-DLP",
        "message": "API funcionando!"
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/play")
def play(query: str, request: Request):
    if not query.strip():
        raise HTTPException(400, "Digite o nome da música")

    shutil.copyfile(
        "/etc/secrets/cookies.txt",
        "/tmp/cookies.txt"
    )

    options = {
        "cookiefile": "/tmp/cookies.txt",
        "format": "bestaudio/best",
        "outtmpl": os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "js_runtimes": {
    "node": {}
},
        "extractor_args": {
    "youtubepot-bgutilscript": {
        "server_home": [
            "/root/bgutil-ytdlp-pot-provider/server"
        ]
    }
},
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "128",
        }],
    }

    try:
        with YoutubeDL(options) as ydl:
            result = ydl.extract_info(
                "ytsearch1:" + query,
                download=True
            )

            if not result or not result.get("entries"):
                raise HTTPException(404, "Música não encontrada")

            video = result["entries"][0]
            video_id = video["id"]
            audio_path = os.path.join(
                DOWNLOAD_DIR, video_id + ".mp3"
            )

            if not os.path.isfile(audio_path):
                raise HTTPException(500, "Falha ao gerar áudio")

            file_id = str(uuid.uuid4())

            with lock:
                files[file_id] = {
                    "path": audio_path,
                    "created": time.time()
                }

            return {
                "title": video.get("title", ""),
                "description": video.get("description", ""),
                "channel": {
                    "name": video.get("channel", "")
                    or video.get("uploader", "")
                },
                "total_duration_in_seconds": video.get("duration", 0),
                "thumbnail": video.get("thumbnail", ""),
                "url": str(request.base_url).rstrip("/") + "/files/" + file_id
            }

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(500, str(error))


@app.get("/files/{file_id}")
def get_file(file_id: str):
    with lock:
        item = files.get(file_id)

    if not item:
        raise HTTPException(404, "Arquivo não encontrado")

    if time.time() - item["created"] > 3600:
        with lock:
            files.pop(file_id, None)
        raise HTTPException(404, "Link expirado")

    if not os.path.isfile(item["path"]):
        raise HTTPException(404, "Áudio não encontrado")

    return FileResponse(
        item["path"],
        media_type="audio/mpeg",
        filename="musica.mp3"
          )
  
