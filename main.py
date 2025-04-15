from fastapi import FastAPI, UploadFile, Form, Request, File
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request
import os
import uuid
import shutil


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
    return FileResponse(os.path.join(UPLOAD_DIR, filename), media_type="audio/mpeg")

@app.get("/", response_class=HTMLResponse)
async def get_index():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/chat")
async def chat(
    message: str = Form(""),
    audio: UploadFile = File(None)
):
    audio_url = None

    # Salvar áudio se existir
    if audio:
        filename = f"{uuid.uuid4()}.webm"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            shutil.copyfileobj(audio.file, f)
        audio_url = f"/audio/{filename}"

    # Enviar para o n8n
    try:
        n8n_url = "https://n8n-project-hedley.onrender.com/webhook-test/apychat"
        payload = {"mensagem": message, "audio": audio_url}
        response = requests.post(n8n_url, json=payload)
        print("Resposta do n8n:", response.text)
    except Exception as e:
        print("Erro ao enviar para o n8n:", e)

    return {
        "received_text": message,
        "received_audio": audio_url
    }

# Servir arquivos de áudio
app.mount("/audio", StaticFiles(directory=UPLOAD_DIR), name="audio")

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def get_index():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()
