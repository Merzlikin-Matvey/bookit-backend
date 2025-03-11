import uuid
from server.backend.redis import get_redis_client

class TelegramConnect:
    def __init__(self):
        self.redis_client = get_redis_client(1)

    async def validate_token(self, user_id, token):
        user_id = str(user_id)
        token_from_user = await self._get_token_from_redis(user_id)
        user_from_token = await self._get_user_from_token(token)
        return token == token_from_user and user_id == user_from_token

    async def get_token(self, user_id):
        user_id = str(user_id)
        if await self._is_token_in_redis(user_id):
            return await self._get_token_from_redis(user_id)
        else:
            token = uuid.uuid4().hex
            await self._set_token_to_redis(user_id, token)
            return token
     
    async def get_user_from_token(self, token):
        return await self._get_user_from_token(token)

    async def _get_user_from_token(self, token):
        value = await self.redis_client.get(token)
        if value:
            return value.decode() if isinstance(value, bytes) else value
        return None   

    async def _get_token_from_redis(self, user_id):
        user_id = str(user_id)
        value = await self.redis_client.get(user_id)
        if value:
            return value.decode() if isinstance(value, bytes) else value
        return None

    async def _is_token_in_redis(self, user_id):
        user_id = str(user_id)
        return await self.redis_client.exists(user_id)

    async def _set_token_to_redis(self, user_id, token, ex=60):
        user_id = str(user_id)
        await self.redis_client.set(user_id, token, ex=ex)
        await self.redis_client.set(token, user_id, ex=ex)