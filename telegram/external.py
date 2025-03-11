import aiohttp
from typing import Tuple, Dict

async def validate_token(token: str) -> Tuple[bool, str]:
    url = "http://server:8080/api/telegram/validate_token"
    params = {"token": token}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status != 200:
                response_text = await response.text()
                raise Exception(f"Request failed with status {response.status}: {response_text}")
            data = await response.json()
            valid = data.get("valid", False)
            returned_user_id = data.get("user_id", "")
            return valid, returned_user_id

async def integrate_user(token: str, telegram_id: str) -> dict:
    url = "http://server:8080/api/telegram/connect"
    payload = {"token": token, "telegram_id": telegram_id}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            return {"status": response.status, "data": await response.json()}

async def check_user_exists(telegram_id: str) -> Dict:
    url = "http://server:8080/api/telegram/exists"
    params = {"telegram_id": telegram_id}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            return await resp.json()