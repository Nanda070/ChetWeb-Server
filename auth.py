import os
import httpx
import jwt
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()
security = HTTPBearer()

# Загружаем всё из .env
CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")
FRONTEND_URL = os.getenv("FRONTEND_URL")
JWT_SECRET = os.getenv("JWT_SECRET")
BOT_TOKEN = os.getenv("BOT_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
ADMIN_ROLE_ID = os.getenv("ADMIN_ROLE_ID")

@router.get("/login")
def login():
    discord_oauth_url = (
        f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify"
    )
    return RedirectResponse(discord_oauth_url)

@router.get("/auth/callback")
async def auth_callback(code: str):
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    
    async with httpx.AsyncClient() as client:
        # 1. Получаем токен пользователя
        token_res = await client.post("https://discord.com/api/oauth2/token", data=data)
        if token_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Discord Auth Error")
        
        access_token = token_res.json().get("access_token")

        # 2. Получаем ID пользователя
        user_res = await client.get("https://discord.com/api/users/@me", 
                                    headers={"Authorization": f"Bearer {access_token}"})
        user_data = user_res.json()
        user_id = user_data.get("id")

        # 3. Проверка прав (Бот запрашивает данные о члене сервера)
        member_res = await client.get(
            f"https://discord.com/api/guilds/{GUILD_ID}/members/{user_id}",
            headers={"Authorization": f"Bot {BOT_TOKEN}"}
        )
        
        if member_res.status_code == 404:
            raise HTTPException(status_code=403, detail=f"User not found on Guild {GUILD_ID}")
        
        member_data = member_res.json()
        roles = member_data.get("roles", [])

        if ADMIN_ROLE_ID not in roles:
            raise HTTPException(status_code=403, detail="Role access denied")

        # 4. Выпуск JWT
        payload = {
            "user_id": user_id,
            "username": user_data.get("username"),
            "exp": datetime.utcnow() + timedelta(hours=12)
        }
        jwt_token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

        return RedirectResponse(f"{FRONTEND_URL}/login?token={jwt_token}")

# Валидатор токена для защищенных роутов
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Проверяет JWT токен из заголовков запроса"""
    try:
        # PyJWT версии 2.x требует указания algorithms в виде списка
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Время жизни токена истекло")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Неверный токен доступа")