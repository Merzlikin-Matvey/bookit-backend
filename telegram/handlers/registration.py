from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from telegram.external import check_user_exists, integrate_user
from telegram.form import AccessTokenForm

router = Router()

@router.message(Command(commands=['start']))
async def send_welcome_handler(message: types.Message, state: FSMContext):
    telegram_id = str(message.from_user.id)
    exists_result = await check_user_exists(telegram_id)
    if exists_result.get("exists"):
        await message.answer("Вы уже синхронизированы")
    else:
        await message.answer("Введите токен доступа (токен вы можете найти здесь \n https://prod-team-17-61ojpp1i.final.prodcontest.ru):")
        await state.set_state(AccessTokenForm.token)

@router.message(AccessTokenForm.token)
async def process_token_handler(message: types.Message, state: FSMContext):
    token = message.text.strip()
    telegram_id = str(message.from_user.id)
    result = await integrate_user(token, telegram_id)
    if result["status"] == 200:
        await message.answer("Интеграция выполнена успешно!")
        await state.clear()
    else:
        await message.answer(f"Ошибка интеграции: {result['data'].get('detail', 'Unknown error')}")
