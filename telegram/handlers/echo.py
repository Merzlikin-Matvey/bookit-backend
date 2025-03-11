from aiogram import Router, types

router = Router()

@router.message()
async def echo_handler(message: types.Message):
    await message.answer(message.text)
