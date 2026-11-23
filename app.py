import os, json, hmac, hashlib, sqlite3, urllib.parse
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
ROOT = Path(__file__).parent
DB = ROOT / "store.db"
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_KEY = os.getenv("ADMIN_KEY", "change-this-admin-key")
WEBAPP_URL = os.getenv("WEBAPP_URL", "")

app = FastAPI(title="RU iOS Store")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

SEED = [
    ("СберБанк", "Банки", "Официальная страница приложения и доступные способы установки.", "https://www.sberbank.ru/", "Сбер"),
    ("Т-Банк", "Банки", "Официальный сайт Т-Банка.", "https://www.tbank.ru/", "Т-Банк"),
    ("ВКонтакте", "Социальные сети", "Официальный сайт социальной сети.", "https://vk.com/", "VK"),
    ("Ozon", "Магазины", "Официальный интернет-магазин.", "https://www.ozon.ru/", "Ozon"),
    ("Госуслуги", "Государственные сервисы", "Официальный портал государственных услуг.", "https://www.gosuslugi.ru/", "Минцифры России"),
    ("Яндекс Музыка", "Музыка и видео", "Официальная страница сервиса.", "https://music.yandex.ru/", "Яндекс"),
    ("Яндекс Go", "Такси и доставка", "Официальная страница сервиса поездок и доставки.", "https://go.yandex/", "Яндекс"),
    ("Игры для iPhone", "Игры", "Откройте каталог игр в App Store.", "https://www.apple.com/ru/app-store/", "Разные разработчики"),
    ("Полезные приложения", "Полезные приложения", "Подборка и поиск приложений в App Store.", "https://www.apple.com/ru/app-store/", "Разные разработчики"),
]

def db():
    con=sqlite3.connect(DB)
    con.row_factory=sqlite3.Row
    return con

def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS apps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, category TEXT NOT NULL, description TEXT NOT NULL,
            url TEXT NOT NULL, developer TEXT NOT NULL, icon TEXT DEFAULT '📱',
            active INTEGER DEFAULT 1
        )""")
        if con.execute("SELECT COUNT(*) FROM apps").fetchone()[0] == 0:
            for name,cat,desc,url,dev in SEED:
                con.execute("INSERT INTO apps(name,category,description,url,developer,icon) VALUES(?,?,?,?,?,?)",
                            (name,cat,desc,url,dev,"📱"))

init_db()

def valid_telegram_init_data(init_data: str) -> bool:
    if not BOT_TOKEN or not init_data:
        return False
    try:
        pairs=dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
        received=pairs.pop("hash")
        check="\\n".join(f"{k}={v}" for k,v in sorted(pairs.items()))
        secret=hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated=hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(calculated, received)
    except Exception:
        return False

class AppIn(BaseModel):
    name: str
    category: str
    description: str
    url: str
    developer: str = "Не указан"
    icon: str = "📱"

@app.get("/")
def home():
    return FileResponse(ROOT / "static" / "index.html")

@app.get("/api/apps")
def list_apps(category: str | None = None, q: str | None = None):
    sql="SELECT * FROM apps WHERE active=1"
    args=[]
    if category and category != "Все":
        sql += " AND category=?"; args.append(category)
    if q:
        sql += " AND (name LIKE ? OR description LIKE ? OR developer LIKE ?)"
        args += [f"%{q}%"]*3
    sql += " ORDER BY category,name"
    with db() as con:
        rows=con.execute(sql,args).fetchall()
    return [dict(r) for r in rows]

@app.get("/api/categories")
def categories():
    with db() as con:
        return [r[0] for r in con.execute("SELECT DISTINCT category FROM apps WHERE active=1 ORDER BY category")]

@app.post("/api/admin/apps")
def add_app(item: AppIn, x_admin_key: str = Header(default="")):
    if not hmac.compare_digest(x_admin_key, ADMIN_KEY):
        raise HTTPException(401,"Неверный ключ администратора")
    if not item.url.startswith("https://"):
        raise HTTPException(400,"Разрешены только HTTPS-ссылки")
    with db() as con:
        cur=con.execute("INSERT INTO apps(name,category,description,url,developer,icon) VALUES(?,?,?,?,?,?)",
                        (item.name,item.category,item.description,item.url,item.developer,item.icon))
        return {"id":cur.lastrowid,"ok":True}

@app.delete("/api/admin/apps/{app_id}")
def delete_app(app_id: int, x_admin_key: str = Header(default="")):
    if not hmac.compare_digest(x_admin_key, ADMIN_KEY):
        raise HTTPException(401,"Неверный ключ администратора")
    with db() as con:
        con.execute("UPDATE apps SET active=0 WHERE id=?",(app_id,))
    return {"ok":True}

@app.get("/health")
def health():
    return {"ok":True}

# Telegram bot polling (optional): set BOT_TOKEN and run `python bot.py`
