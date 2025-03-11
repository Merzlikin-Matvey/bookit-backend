import os
import uuid
import logging
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
import aiohttp
from yarl import URL

from server.backend.database import get_session
from server.services.auth import Auth
from server.repositories.user import UserRepository
from server.backend.redis import get_redis_client

redis_client = get_redis_client(0)

router = APIRouter(prefix="/yandex", tags=["yandex"])
logger = logging.getLogger(__name__)

CLIENT_ID = os.getenv("YANDEX_CLIENT_ID")
CLIENT_SECRET = os.getenv("YANDEX_CLIENT_SECRET")
REDIRECT_URI = os.getenv("YANDEX_REDIRECT_URI")
FRONTEND_CALLBACK_URL = os.getenv("FRONTEND_CALLBACK_URL")
if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI or not FRONTEND_CALLBACK_URL:
    raise Exception("Отсутствуют необходимые переменные окружения для Яндекс OAuth.")

YANDEX_AUTHORIZE_URL = "https://oauth.yandex.ru/authorize"
YANDEX_TOKEN_URL = "https://oauth.yandex.ru/token"
YANDEX_USERINFO_URL = "https://login.yandex.ru/info"

ACCESS_TOKEN_EXPIRE_SECONDS = 3600  # 1 час
REFRESH_TOKEN_EXPIRE_SECONDS = 2592000  # 30 дней
CODE_TTL = 300  # TTL для кода (5 минут)


@router.get("/login", summary="Вход через Яндекс")
async def yandex_login():
    state = str(uuid.uuid4())
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "state": state,
    }
    auth_url = URL(YANDEX_AUTHORIZE_URL).with_query(params)
    response = RedirectResponse(str(auth_url))
    response.set_cookie(key="yandex_state", value=state, max_age=CODE_TTL, httponly=True)
    return response


@router.get("/callback", summary="Callback Яндекс OAuth")
async def yandex_callback(request: Request, code: str, state: str, db: AsyncSession = Depends(get_session)):
    cookie_state = request.cookies.get("yandex_state")
    if not cookie_state or cookie_state != state:
        logger.error("Некорректное состояние (state) в запросе.")
        return RedirectResponse(url="/yandex/login?error=invalid_state")

    used_code_key = f"yandex:code:{code}"
    if await redis_client.get(used_code_key):
        logger.info(f"Код {code} уже был использован.")
        return RedirectResponse(url="/yandex/login?error=auth_again")
    await redis_client.set(used_code_key, "used", ex=CODE_TTL)

    try:
        token_payload = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        async with aiohttp.ClientSession() as session:
            async with session.post(YANDEX_TOKEN_URL, data=token_payload, headers=headers) as token_resp:
                if token_resp.status != 200:
                    logger.error(f"Ошибка при получении токена: статус {token_resp.status}")
                    return RedirectResponse(url="/yandex/login?error=auth_again")
                token_data = await token_resp.json()

            access_token_yandex = token_data.get("access_token")
            if not access_token_yandex:
                logger.error("Отсутствует access_token в ответе от Яндекс.")
                return RedirectResponse(url="/yandex/login?error=auth_again")

            auth_header = {"Authorization": f"OAuth {access_token_yandex}"}
            async with session.get(YANDEX_USERINFO_URL, headers=auth_header) as userinfo_resp:
                if userinfo_resp.status != 200:
                    logger.error(f"Ошибка при получении информации о пользователе: статус {userinfo_resp.status}")
                    return RedirectResponse(url="/yandex/login?error=auth_again")
                yandex_user = await userinfo_resp.json()

        yandex_id = yandex_user.get("id")
        if not yandex_id:
            logger.error("Отсутствует идентификатор пользователя в данных Яндекс.")
            return RedirectResponse(url="/yandex/login?error=auth_again")

        user_repo = UserRepository(db)
        db_user = await user_repo.get_by_yandex_id(yandex_id)
        if not db_user:
            email_from_yandex = yandex_user.get("default_email") or yandex_user.get("email")
            if email_from_yandex:
                db_user = await user_repo.get_by_email(email_from_yandex)
            if db_user:
                if not db_user.yandex_id:
                    db_user = await user_repo.update_user(db_user.id, {"yandex_id": yandex_id})
            else:
                db_user = await user_repo.create_user_yandex(yandex_user)

        new_access_token = Auth().create_access_token(data={"sub": str(db_user.id)})
        new_refresh_token = Auth().create_refresh_token(data={"sub": str(db_user.id)})

        await redis_client.set(f"user:{db_user.id}:access_token", new_access_token, ex=ACCESS_TOKEN_EXPIRE_SECONDS)
        await redis_client.set(f"user:{db_user.id}:refresh_token", new_refresh_token, ex=REFRESH_TOKEN_EXPIRE_SECONDS)

        redirect_url = f"{FRONTEND_CALLBACK_URL}?access_token={new_access_token}"
        response = RedirectResponse(redirect_url, status_code=303)
        response.delete_cookie("yandex_state")
        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            max_age=ACCESS_TOKEN_EXPIRE_SECONDS,
            expires=ACCESS_TOKEN_EXPIRE_SECONDS,
            path="/",
            secure=False
        )
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            max_age=REFRESH_TOKEN_EXPIRE_SECONDS,
            expires=REFRESH_TOKEN_EXPIRE_SECONDS,
            path="/",
            secure=False
        )
        return response

    except Exception as e:
        logger.exception("Ошибка в процессе авторизации через Яндекс OAuth:")
        await redis_client.delete(used_code_key)
        return RedirectResponse(url="/yandex/login?error=server_error")
