from fastapi import APIRouter
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.exceptions import RequestValidationError
from server.routers.auth import router as auth_router
from server.routers.yandex_auth import router as yandex_router
from server.routers.user import router as user_router
from server.routers.seat import router as seat_router
from server.routers.reservation import router as reservation_router
from server.routers.admin_panel import router as admin_panel_router
from server.routers.ticket import router as ticket_router
from server.routers.test import router as test_router
from server.routers.telegram_connect import router as telegram_router
from server.routers.metrics import router as metrics_router
from server.routers.avatar import router as avatar_router
from server.routers.stats import router as stats_router

app = FastAPI(
    title="Final PROD",
    version="0.0.1",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

origins = [
    "http://localhost:3000",
    "https://prod-team-17-61ojpp1i.final.prodcontest.ru"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def docs_redirect():
    return RedirectResponse(url="/api/docs")



@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print("Ошибка 400: Неверный запрос. Детали:", exc.errors())
    return JSONResponse(
        status_code=400,
        content={"detail": "Ошибка валидации", "errors": exc.errors()}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print("Ошибка 422: Неверный запрос. Дополнительная информация:", exc.errors())
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Ошибка валидации",
            "errors": exc.errors(),
            "extra_info": "Дополнительная информация по ошибке 422"
        }
    )


api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(yandex_router)
api_router.include_router(user_router)
api_router.include_router(seat_router)
api_router.include_router(reservation_router)
api_router.include_router(admin_panel_router)
api_router.include_router(ticket_router)
api_router.include_router(test_router)
api_router.include_router(telegram_router)
api_router.include_router(metrics_router)
api_router.include_router(avatar_router)
api_router.include_router(stats_router)

app.include_router(api_router)

# docker compose exec server alembic revision --autogenerate -m "Initial migration"
# docker compose exec server alembic upgrade head
