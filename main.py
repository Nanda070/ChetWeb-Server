import os
import sqlite3
import random
import subprocess
import psutil
import httpx
import datetime
from collections import deque
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from sqlalchemy.orm import Session

import models
from database import engine, get_db
from auth import router as auth_router, get_current_user

models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="404 Control Tower API", version="1.7.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth_router)

# --- СХЕМЫ ---
class ConfigUpdate(BaseModel): key: str; value: str
class LogEntry(BaseModel): source_bot: str; action: str; user_id: Optional[str] = None; details: Optional[str] = None
class TicketResolve(BaseModel): action: str
class TicketCreate(BaseModel): user_id: str; content: str
class BotAction(BaseModel): action: str

class EmbedField(BaseModel): name: str; value: str; inline: bool = False
class EmbedPayload(BaseModel): channel_id: str; content: Optional[str] = None; title: Optional[str] = None; description: Optional[str] = None; url: Optional[str] = None; color: Optional[str] = "#B75CFF"; author_name: Optional[str] = None; author_icon: Optional[str] = None; author_url: Optional[str] = None; image_url: Optional[str] = None; thumbnail_url: Optional[str] = None; footer_text: Optional[str] = None; footer_icon: Optional[str] = None; timestamp: Optional[bool] = False; fields: Optional[List[EmbedField]] = []

# --- ИНФРАСТРУКТУРА БОТОВ (Добавлен log_file) ---
BOTS_REGISTRY = {
    "chet_supply": {"name": "ChetSupply", "command": ["python", "test_bot.py", "chet_supply"], "log_file": "chet_supply.log", "process": None},
    "chet_voice": {"name": "ChetVoice", "command": ["python", "test_bot.py", "chet_voice"], "log_file": "chet_voice.log", "process": None},
}

def get_real_rooms_count():
    db_path = "private_rooms.db"
    if not os.path.exists(db_path): return "N/A"
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%room%';")
            table = cursor.fetchone()
            if table:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                return cursor.fetchone()[0]
    except: pass
    return 0

@app.get("/api/health")
async def health_check(): return {"status": "Online"}

@app.get("/api/dashboard/stats")
async def get_dashboard_stats(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"admin_name": user.get("username"), "active_rooms": get_real_rooms_count(), "pending_feedbacks": db.query(models.FeedbackCase).filter(models.FeedbackCase.status == "pending").count()}

@app.get("/api/infrastructure/bots")
async def get_bots_status(user: dict = Depends(get_current_user)):
    status_list = []
    for bot_id, data in BOTS_REGISTRY.items():
        proc = data["process"]
        is_running, ram = False, "0 MB"
        if proc is not None and proc.poll() is None:
            is_running = True
            try: ram = f"{psutil.Process(proc.pid).memory_info().rss / 1024 / 1024:.1f} MB"
            except: pass
        status_list.append({"id": bot_id, "name": data["name"], "status": "ONLINE" if is_running else "OFFLINE", "ram": ram})
    return status_list

@app.post("/api/infrastructure/bots/{bot_id}/action")
async def manage_bot(bot_id: str, payload: BotAction, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if bot_id not in BOTS_REGISTRY: raise HTTPException(status_code=404)
    bot_data = BOTS_REGISTRY[bot_id]
    proc = bot_data["process"]
    if payload.action == "start":
        if proc is None or proc.poll() is not None: bot_data["process"] = subprocess.Popen(bot_data["command"])
    elif payload.action == "stop":
        if proc is not None and proc.poll() is None: proc.terminate(); proc.wait()
    elif payload.action == "restart":
        if proc is not None and proc.poll() is None: proc.terminate(); proc.wait()
        bot_data["process"] = subprocess.Popen(bot_data["command"])
    db.add(models.AuditLog(source_bot="PROCESS_MANAGER", action=f"BOT_{payload.action.upper()}", user_id=user.get("username"), details=f"Target: {bot_data['name']}"))
    db.commit()
    return {"status": "success"}

# --- НОВЫЙ ЭНДПОИНТ: ЧТЕНИЕ ЛОГОВ ИЗ ФАЙЛА ---
@app.get("/api/infrastructure/bots/{bot_id}/logs")
async def get_bot_logs(bot_id: str, user: dict = Depends(get_current_user)):
    if bot_id not in BOTS_REGISTRY: raise HTTPException(status_code=404)
    log_file = BOTS_REGISTRY[bot_id].get("log_file")
    if not log_file or not os.path.exists(log_file):
        return {"logs": "Файл логов не найден или пуст. Запустите бота."}
    
    # Читаем последние 50 строк (быстро и не перегружает память)
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = deque(f, 50)
            return {"logs": "".join(lines)}
    except Exception as e:
        return {"logs": f"Ошибка чтения лога: {str(e)}"}

def validate_url(url: Optional[str], field_name: str) -> Optional[str]:
    if not url: return None
    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")): raise HTTPException(status_code=400, detail=f"[{field_name}] Некорректный URL. Должен начинаться с http:// или https://")
    return url

@app.post("/api/announcer/send")
async def send_custom_embed(payload: EmbedPayload, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token: raise HTTPException(status_code=500, detail="BOT_TOKEN не настроен")
    if not payload.channel_id: raise HTTPException(status_code=400, detail="Не указан ID канала")

    embed_data = {}
    if payload.title: embed_data["title"] = payload.title
    if payload.description: embed_data["description"] = payload.description
    url = validate_url(payload.url, "MAIN_URL")
    if url: embed_data["url"] = url
    try: embed_data["color"] = int(payload.color.lstrip('#'), 16)
    except: embed_data["color"] = 0

    if payload.author_name:
        embed_data["author"] = {"name": payload.author_name}
        author_url = validate_url(payload.author_url, "AUTHOR_URL")
        if author_url: embed_data["author"]["url"] = author_url
        author_icon = validate_url(payload.author_icon, "AUTHOR_ICON")
        if author_icon: embed_data["author"]["icon_url"] = author_icon

    image_url = validate_url(payload.image_url, "IMAGE_URL")
    if image_url: embed_data["image"] = {"url": image_url}
    thumbnail_url = validate_url(payload.thumbnail_url, "THUMBNAIL_URL")
    if thumbnail_url: embed_data["thumbnail"] = {"url": thumbnail_url}

    if payload.footer_text:
        embed_data["footer"] = {"text": payload.footer_text}
        footer_icon = validate_url(payload.footer_icon, "FOOTER_ICON")
        if footer_icon: embed_data["footer"]["icon_url"] = footer_icon

    if payload.timestamp: embed_data["timestamp"] = datetime.datetime.utcnow().isoformat()
    if payload.fields: embed_data["fields"] = [{"name": f.name, "value": f.value, "inline": f.inline} for f in payload.fields]

    discord_payload = {}
    if payload.content: discord_payload["content"] = payload.content
    if embed_data: discord_payload["embeds"] = [embed_data]

    headers = {"Authorization": f"Bot {bot_token}", "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        res = await client.post(f"https://discord.com/api/v10/channels/{payload.channel_id}/messages", json=discord_payload, headers=headers)
        
    if res.status_code != 200: raise HTTPException(status_code=400, detail=f"Discord API Error: {res.text}")
    db.add(models.AuditLog(source_bot="ANNOUNCER", action="EMBED_SENT", user_id=user.get("username"), details=f"Channel {payload.channel_id}"))
    db.commit()
    return {"status": "success"}

@app.get("/api/config")
async def get_config(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    configs = db.query(models.GlobalConfig).all()
    if not configs:
        db.bulk_save_objects([
            models.GlobalConfig(key="TARGET_ROLE_ID", value="1503414541206290673", description="ID Роли"),
            models.GlobalConfig(key="LOG_CHANNEL_ID", value="1503425312409780344", description="ID Канала логов"),
            models.GlobalConfig(key="VOICE_CHANNEL_ID", value="1503414991842185296", description="ID Голосового канала")
        ])
        db.commit()
        configs = db.query(models.GlobalConfig).all()
    return [{"key": c.key, "value": c.value, "description": c.description} for c in configs]

@app.post("/api/config")
async def update_config(item: ConfigUpdate, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    config_item = db.query(models.GlobalConfig).filter(models.GlobalConfig.key == item.key).first()
    if not config_item: raise HTTPException(status_code=404)
    old_value = config_item.value
    config_item.value = item.value
    db.add(models.AuditLog(source_bot="DASHBOARD_CORE", action="CONFIG_UPDATE", user_id=user.get("username"), details=f"Changed {item.key} from {old_value} to {item.value}"))
    db.commit()
    return {"status": "success"}

@app.post("/api/audit")
async def create_audit_log(entry: LogEntry, db: Session = Depends(get_db)):
    db.add(models.AuditLog(**entry.dict()))
    db.commit()
    return {"status": "logged"}

@app.get("/api/audit")
async def get_audit_logs(limit: int = 50, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    logs = db.query(models.AuditLog).order_by(models.AuditLog.timestamp.desc()).limit(limit).all()
    return [{"id": l.id, "source_bot": l.source_bot, "action": l.action, "user_id": l.user_id, "details": l.details, "timestamp": l.timestamp.strftime("%Y-%m-%d %H:%M:%S") if l.timestamp else "N/A"} for l in logs]

@app.post("/api/moderation/tickets/create")
async def create_ticket(ticket: TicketCreate, db: Session = Depends(get_db)):
    cols = models.FeedbackCase.__table__.columns.keys()
    new_case = models.FeedbackCase(status="pending")
    if "submitter_id" in cols: new_case.submitter_id = ticket.user_id
    elif "user_id" in cols: new_case.user_id = ticket.user_id
    for f in ["reason", "description", "message", "content", "text", "category"]:
        if f in cols: setattr(new_case, f, ticket.content); break
    if "case_id" in cols: new_case.case_id = random.randint(100000, 999999)
    db.add(new_case)
    db.commit()
    tid = getattr(new_case, 'case_id', getattr(new_case, 'id', 'UNKNOWN'))
    db.add(models.AuditLog(source_bot="DISCORD_BOT", action="NEW_TICKET", user_id=ticket.user_id, details=f"Ticket #{tid} created"))
    db.commit()
    return {"status": "success"}

@app.get("/api/moderation/tickets")
async def get_tickets(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    tickets = db.query(models.FeedbackCase).filter(models.FeedbackCase.status == "pending").all()
    return [{"id": getattr(t, 'case_id', getattr(t, 'id', 0)), "user_id": getattr(t, 'submitter_id', getattr(t, 'user_id', 'Unknown')), "content": getattr(t, 'reason', getattr(t, 'description', getattr(t, 'message', getattr(t, 'text', getattr(t, 'category', ''))))), "status": t.status} for t in tickets]

@app.post("/api/moderation/tickets/{ticket_id}/resolve")
async def resolve_ticket(ticket_id: str, payload: TicketResolve, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    cols = models.FeedbackCase.__table__.columns.keys()
    ticket = db.query(models.FeedbackCase).filter(models.FeedbackCase.case_id == ticket_id).first() if "case_id" in cols else db.query(models.FeedbackCase).filter(models.FeedbackCase.id == ticket_id).first()
    if not ticket: raise HTTPException(status_code=404)
    ticket.status = "approved" if payload.action == "approve" else "denied"
    db.add(models.AuditLog(source_bot="DASHBOARD_CORE", action="TICKET_RESOLVED", user_id=user.get("username"), details=f"Ticket #{ticket_id} marked as {payload.action.upper()}"))
    db.commit()
    return {"status": "success"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)