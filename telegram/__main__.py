import asyncio
import os
from aiogram import Bot, Dispatcher
from fastapi import FastAPI, BackgroundTasks, HTTPException  # added import
import uvicorn

# Update imports to use absolute paths from project root
from telegram.handlers.registration import router as registration_router
from telegram.handlers.echo import router as echo_router 

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(registration_router)
dp.include_router(echo_router)

# Create FastAPI app
app = FastAPI(title="Telegram Bot API")

# Bot running flag
bot_running = False

async def start_bot():
    global bot_running
    if not bot_running:
        bot_running = True
        print("Бот работает", flush=True)
        try:
            await dp.start_polling(bot)
        except Exception as e:
            print(f"Ошибка бота: {e}", flush=True)
        finally:
            bot_running = False

@app.post("/start_bot")
async def api_start_bot(background_tasks: BackgroundTasks):
    global bot_running
    if bot_running:
        return {"status": "Бот уже запущен"}
    
    background_tasks.add_task(start_bot)
    return {"status": "Бот запускается"}

@app.post("/send_message")
async def send_message(payload: dict):
    telegram_id = payload.get("telegram_id")
    message = payload.get("message")
    if not telegram_id or not message:
        raise HTTPException(status_code=400, detail="Отсутствует telegram_id или message")
    try:
        await bot.send_message(chat_id=telegram_id, text=message)
        return {"status": "Сообщение отправлено"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def status():
    return {"status": "ok", "bot_running": bot_running}

async def main():
    await start_bot()

