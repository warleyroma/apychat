from fastapi import FastAPI, UploadFile, Form, File, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import shutil
import requests
import httpx

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

# Servir arquivos de áudio
app.mount("/audio", StaticFiles(directory=UPLOAD_DIR), name="audio")

@app.get("/")
def render_chat(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.isfile(file_path):
        return FileResponse(file_path, media_type="audio/ogg")
    return {"error": "Arquivo não encontrado."}

@app.post("/chat/text")
async def chat_text(message: str = Form(...), env: str = Form(...)):
    try:
        if env == "production":
            n8n_url = "https://n8n-project-hedley.onrender.com/webhook/apychat"
        else:
            n8n_url = "https://n8n-project-hedley.onrender.com/webhook-test/apychat"

        payload = {"message": {"text": message}}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(n8n_url, json=payload)

        if response.status_code == 200:
            try:
                resposta_data = response.json()

                if isinstance(resposta_data, list) and len(resposta_data) > 0 and "text" in resposta_data[0]:
                    resposta_n8n = resposta_data[0]["text"]
                else:
                    resposta_n8n = resposta_data

            except Exception:
                resposta_n8n = {"text": response.text}
        else:
            resposta_n8n = {"error": f"Erro ao se comunicar com o n8n. Status: {response.status_code}"}

    except Exception as e:
        resposta_n8n = {"error": str(e)}

    return {
        "received_text": message,
        "response": resposta_n8n
    }

@app.post("/chat/audio")
async def chat_audio(file: UploadFile = File(...), env: str = Form(...)):
    filename = f"voice_{uuid.uuid4().hex}.ogg"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if env == "production":
        n8n_url = "https://n8n-project-hedley.onrender.com/webhook/apychat"
    else:
        n8n_url = "https://n8n-project-hedley.onrender.com/webhook-test/apychat"

    try:
        # Envia o arquivo de áudio diretamente como multipart
        with open(file_path, "rb") as audio_file:
            files = {
                "file": (filename, audio_file, "audio/ogg")
            }
            response = requests.post(n8n_url, files=files)
            print("Resposta do n8n:", response.text)

    if response.status_code == 200:
                try:
                    resposta_data = response.json()

                    if isinstance(resposta_data, list) and len(resposta_data) > 0 and "text" in resposta_data[0]:
                        resposta_n8n = resposta_data[0]["text"]
                    else:
                        resposta_n8n = resposta_data
                except Exception:
                    resposta_n8n = {"text": response.text}
            else:
                resposta_n8n = {"error": f"Erro ao se comunicar com o n8n. Status: {response.status_code}"}
                
    except Exception as e:
        print("Erro ao enviar para o n8n:", e)
        resposta_n8n = {"error": str(e)}
    return {
        "message": "Áudio recebido com sucesso",
        "audio_url": f"/audio/{filename}"
        "response": resposta_n8n
    }

