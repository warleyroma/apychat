from fastapi import FastAPI, UploadFile, Form, File, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import shutil
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Configurar templates e arquivos estáticos
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def render_chat(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    return FileResponse(os.path.join(UPLOAD_DIR, filename), media_type="audio/webm")

# ✅ Endpoint para enviar texto corrigido
@app.post("/chat/text")
async def chat_text(message: str = Form(...)):
    try:
        n8n_url = "https://n8n-project-hedley.onrender.com/webhook-test/apychat"
        payload = { "message": { "text": message } }

        response = requests.post(n8n_url, json=payload)
        response.raise_for_status()

        try:
            resposta_n8n = response.json()
        except Exception:
            resposta_n8n = {"text": response.text}

        # Se a resposta for uma lista, pegar o primeiro texto
        if isinstance(resposta_n8n, list) and "text" in resposta_n8n[0]:
            reply = resposta_n8n[0]["text"]
        elif isinstance(resposta_n8n, dict) and "text" in resposta_n8n:
            reply = resposta_n8n["text"]
        else:
            reply = str(resposta_n8n)

    except Exception as e:
        reply = f"Erro ao se comunicar com o agente: {e}"

    return {
        "reply": reply
    }

@app.post("/chat/audio")
async def chat_audio(file: UploadFile = File(...)):
    # Salva o arquivo de áudio temporariamente
    filename = f"voice_{uuid.uuid4().hex}.webm"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Enviar para o n8n
    try:
        n8n_url = "https://n8n-project-hedley.onrender.com/webhook-test/apychat"
        payload = {"voice": f"/audio/{filename}"}
        response = requests.post(n8n_url, json=payload)
        print("Resposta do n8n:", response.text)
    except Exception as e:
        print("Erro ao enviar para o n8n:", e)

    return {
        "message": "Áudio recebido com sucesso",
        "audio_url": f"/audio/{filename}"
    }

# Servir arquivos de áudio
app.mount("/audio", StaticFiles(directory=UPLOAD_DIR), name="audio")
