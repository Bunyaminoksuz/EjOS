from fastapi import FastAPI, Response, Body
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn
import psutil
import requests
import json
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- VERİTABANI AYARLARI ---
DB_FILE = "chats.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- İSTEK MODELLERİ ---
class ChatRequest(BaseModel):
    message: str

class SaveChatModel(BaseModel):
    id: int
    title: str
    messages: List[Dict[str, Any]]

# --- API ENDPOINTLERİ ---

# 1. GEÇMİŞİ GETİR (Tüm cihazlar buradan okuyacak)
@app.get("/api/history")
async def get_history():
    return load_db()

# 2. SOHBETİ KAYDET (Tüm cihazlar buraya yazacak)
@app.post("/api/save_chat")
async def save_chat(chat: SaveChatModel):
    chats = load_db()
    
    # Var olan sohbeti bul ve güncelle
    found = False
    for i, c in enumerate(chats):
        if c["id"] == chat.id:
            chats[i] = chat.dict() # Güncelle
            # En başa taşı
            updated_chat = chats.pop(i)
            chats.insert(0, updated_chat)
            found = True
            break
    
    # Yoksa yeni ekle
    if not found:
        chats.insert(0, chat.dict())
    
    save_db(chats)
    return {"status": "ok"}

# 3. SOHBET SİL
@app.post("/api/delete_chat")
async def delete_chat(payload: Dict[str, int] = Body(...)):
    chat_id = payload.get("id")
    chats = load_db()
    chats = [c for c in chats if c["id"] != chat_id]
    save_db(chats)
    return {"status": "deleted"}

# 4. MODEL İLE KONUŞMA (Streaming)
def stream_ollama(kullanici_mesaji):
    url = "http://127.0.0.1:11434/api/chat"
    
    # --- SENİN ORİJİNAL PROMPT'UN + LATEX KURALLARI ---
    sistem_talimati = """Sen Ejos. Uzman bir Elektrik-Elektronik Mühendisi, Fizikçi ve Bilim İnsanısın.
    Kullanıcıyla daima Türkçe konuşursun.
    Teknik terimleri (Op-Amp, MOSFET, Quantum vb.) orijinal haliyle kullanıp açıklamalarını Türkçe yaparsın.
    Kısa, net ve çözüm odaklı cevaplar verirsin.

    ÇOK ÖNEMLİ EK KURAL (LATEX FORMATI):
    Matematiksel denklemleri, fizik formüllerini ve bilimsel sayı gösterimlerini ASLA düz metin olarak yazma.
    HER ZAMAN LaTeX formatında ve '$' işaretleri arasında yaz.
    
    Örnekler:
    - Yanlış: E = mc^2 veya 3 x 10^-8
    - Doğru: $E = mc^2$
    - Doğru: $3 \\times 10^{-8}$
    - Doğru: $V_{out} = V_{in} \\cdot (1 + \\frac{R_2}{R_1})$
    """

    payload = {
        "model": "ejos-ai", 
        "messages": [
            {"role": "system", "content": sistem_talimati},
            {"role": "user", "content": kullanici_mesaji}
        ],
        "stream": True,
        "temperature": 0.2, # Biraz kıstık ki formül kurallarına uysun
    }
    
    try:
        with requests.post(url, json=payload, stream=True) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if line:
                    try:
                        json_response = json.loads(line)
                        if "message" in json_response and "content" in json_response["message"]:
                            yield json_response["message"]["content"]
                    except ValueError:
                        continue
    except Exception as e:
        yield f"Hata: {str(e)}"

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    return StreamingResponse(stream_ollama(request.message), media_type="text/plain")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

# --- SİSTEM İSTATİSTİKLERİ VE SICAKLIK ---
def get_temps():
    try:
        temps = psutil.sensors_temperatures()
        if not temps: return {"cpu": 0, "sys": 0}
        cpu_temp = 0
        sys_temp = 0
        if 'coretemp' in temps: cpu_temp = temps['coretemp'][0].current
        elif 'k10temp' in temps: cpu_temp = temps['k10temp'][0].current
        elif 'cpu_thermal' in temps: cpu_temp = temps['cpu_thermal'][0].current
        
        if 'acpitz' in temps: sys_temp = temps['acpitz'][0].current
        elif 'pch_skylake' in temps: sys_temp = temps['pch_skylake'][0].current
        else: sys_temp = cpu_temp 
        return {"cpu": cpu_temp, "sys": sys_temp}
    except: return {"cpu": 0, "sys": 0}

@app.get("/api/stats")
async def get_stats():
    cpu_usage = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory()
    ram_used_gb = round(ram.used / (1024 ** 3), 1)
    ram_total_gb = round(ram.total / (1024 ** 3), 1)
    temperatures = get_temps()
    return {
        "cpu": cpu_usage,
        "ram_percent": ram.percent,
        "ram_text": f"{ram_used_gb} GB / {ram_total_gb} GB",
        "temp_cpu": temperatures["cpu"],
        "temp_sys": temperatures["sys"]
    }

app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)