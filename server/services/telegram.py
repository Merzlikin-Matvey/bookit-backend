import httpx

from server.models.ticket import Ticket
from server.repositories.user import UserRepository


class TelegramSender:
    def __init__(self, db, endpoint: str = "http://telegram:8010/send_message"):
        self.endpoint = endpoint
        self.db = db

    async def send_message(self, telegram_id: str, message: str):
        print("Sending message to", telegram_id)
        payload = {"telegram_id": telegram_id, "message": message}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.endpoint, json=payload)
                return response.status_code == 200
            except Exception:
                return False

    async def send_ticket_to_all_admins(self, ticket: Ticket):
        admins = await UserRepository(self.db).get_all_admins()
        message = self.generate_message(ticket)
        for admin in admins:
            if getattr(admin, "telegram_id", None):
                await self.send_message(admin.telegram_id, message)

    def generate_message(self, ticket: Ticket):
        lines = [
            "Новый тикет",
            f"ID: {ticket.id}",
            f"Пользователь: {ticket.user_id}",
            f"Сообщение: {ticket.message}"
        ]
        width = max(len(line) for line in lines) + 4

        top_border = "============="
        bottom_border = "============="

        result = [top_border]
        for line in lines:
            result.append(line.ljust(width - 4))
        result.append(bottom_border)

        return "\n".join(result)

