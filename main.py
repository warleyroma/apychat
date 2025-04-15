from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import uuid

app = FastAPI()

# Libera acesso de qualquer origem (ajuste depois se quiser)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/chat")
async def chat(message: str = Form(""), audio: UploadFile = None):
    audio_url = None
    if audio:
        filename = f"{uuid.uuid4()}.mp3"
        path = os.path.join(UPLOAD_DIR, filename)
        with open(path, "wb") as f:
            f.write(await audio.read())
        audio_url = f"/audio/{filename}"

    return {
        "received_text": message,
        "received_audio": audio_url
    }

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    return FileResponse(os.path.join(UPLOAD_DIR, filename), media_type="audio/mpeg")
