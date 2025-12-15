from fastapi import FastAPI, Response, Body, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import requests
import json
import os

# Root app: sadece mount işleri (static + api)
app = FastAPI()

# API app: bütün backend endpoint'leri burada
api_app = FastAPI()

api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lenovo hedefleri (ENV ile)
LENOVO_HOST = os.getenv("LENOVO_HOST", "192.168.55.1")
LENOVO_OLLAMA_PORT = os.getenv("LENOVO_OLLAMA_PORT", "11434")
LENOVO_STATS_PORT = os.getenv("LENOVO_STATS_PORT", "9000")

LENOVO_OLLAMA_CHAT = f"http://{LENOVO_HOST}:{LENOVO_OLLAMA_PORT}/api/chat"
LENOVO_STATS_URL = f"http://{LENOVO_HOST}:{LENOVO_STATS_PORT}/stats"

DB_FILE = "chats.json"


def load_db():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


class ChatRequest(BaseModel):
    message: str


class SaveChatModel(BaseModel):
    id: int
    title: str
    messages: List[Dict[str, Any]]


@api_app.get("/history")
async def get_history():
    return load_db()


@api_app.post("/save_chat")
async def save_chat(chat: SaveChatModel):
    chats = load_db()
    found = False

    for i, c in enumerate(chats):
        if c.get("id") == chat.id:
            chats[i] = chat.model_dump()
            updated = chats.pop(i)
            chats.insert(0, updated)
            found = True
            break

    if not found:
        chats.insert(0, chat.model_dump())

    save_db(chats)
    return {"status": "ok"}


@api_app.post("/delete_chat")
async def delete_chat(payload: Dict[str, int] = Body(...)):
    chat_id = payload.get("id")
    chats = [c for c in load_db() if c.get("id") != chat_id]
    save_db(chats)
    return {"status": "deleted"}


def stream_ollama(kullanici_mesaji: str):
    sistem_talimati = (
        "Sen Ejos. Uzman bir Elektrik-Elektronik Mühendisi, Fizikçi ve Bilim İnsanısın. "
        "Kullanıcıyla daima Türkçe konuşursun. Kısa, net ve çözüm odaklı cevaplar verirsin. "
        "Matematiksel denklemleri LaTeX formatında yaz."
    )

    payload = {
        "model": "ejos-ai",
        "messages": [
            {"role": "system", "content": sistem_talimati},
            {"role": "user", "content": kullanici_mesaji},
        ],
        "stream": True,
        "temperature": 0.2,
    }

    try:
        with requests.post(
            LENOVO_OLLAMA_CHAT,
            json=payload,
            stream=True,
            timeout=600,
        ) as r:
            r.raise_for_status()

            for line in r.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                msg = obj.get("message") or {}
                content = msg.get("content")
                if content:
                    yield content

                if obj.get("done") is True:
                    break

    except requests.exceptions.ConnectTimeout as e:
        yield f"\n[Hata: Lenovo Ollama bağlantı timeout: {str(e)}]"
    except requests.exceptions.ConnectionError as e:
        yield f"\n[Hata: Lenovo Ollama bağlantı hatası: {str(e)}]"
    except requests.exceptions.RequestException as e:
        yield f"\n[Hata: Lenovo Ollama istek hatası: {str(e)}]"
    except Exception as e:
        yield f"\n[Hata: {str(e)}]"


@api_app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    return StreamingResponse(stream_ollama(request.message), media_type="text/plain")


@api_app.get("/stats")
async def stats_proxy():
    try:
        r = requests.get(LENOVO_STATS_URL, timeout=2)
        r.raise_for_status()
        return r.json()

    except requests.exceptions.ConnectTimeout:
        raise HTTPException(status_code=504, detail="Lenovo stats bağlantı timeout (connect timeout).")
    except requests.exceptions.ReadTimeout:
        raise HTTPException(status_code=504, detail="Lenovo stats cevap timeout (read timeout).")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=502, detail="Lenovo stats servisine bağlanılamadı (connection error).")
    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Lenovo stats upstream HTTP error: {str(e)}")
    except ValueError:
        raise HTTPException(status_code=502, detail="Lenovo stats JSON formatı geçersiz.")


@api_app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


# API'yi /api altına mount et (static ile çakışmasın). [web:1149][web:875]
app.mount("/api", api_app)

# Static paneli root'a mount et (index.html root'ta açılır). [web:872]
app.mount("/", StaticFiles(directory=".", html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("PANEL_HOST", "0.0.0.0")
    port = int(os.getenv("PANEL_PORT", "8000"))

    # Uvicorn ayarlarında örneklenen import-string çalıştırma biçimi. [web:1078]
    uvicorn.run("main:app", host=host, port=port, log_level="info")
