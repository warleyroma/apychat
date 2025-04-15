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
    return FileResponse(os.path.join(UPLOAD_DIR, filename), media_type="audio/mpeg")

# Endpoint para enviar texto
@app.post("/chat/text")
async def chat_text(message: str = Form(...)):
    # Enviar para o n8n
    try:
        n8n_url = "https://n8n-project-hedley.onrender.com/webhook-test/apychat"
        payload = {"message": {"text": message}}
        response = requests.post(n8n_url, json=payload)

if response.status_code == 200:
   try:
    response = requests.post(n8n_url, json=payload)
    if response.status_code == 200:
        try:
            resposta_n8n = response.json()
        except:
            resposta_n8n = {"text": response.text}
    else:
        resposta_n8n = {"error": "Erro ao se comunicar com o n8n"}
except Exception as e:
    resposta_n8n = {"error": str(e)}

return {
    "received_text": message,
    "response": resposta_n8n
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

    return {"message": "Áudio recebido com sucesso", "audio_url": f"/audio/{filename}"}
# Servir arquivos de áudio
app.mount("/audio", StaticFiles(directory=UPLOAD_DIR), name="audio")

#@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
#async def get_index():
  #  with open("index.html", "r", encoding="utf-8") as f:
#        return f.read()
