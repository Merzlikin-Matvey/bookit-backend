import pytest
import requests
import uuid
from datetime import datetime, timedelta
from data import BASE_URL, ADMIN_KEY, USERS_DATA, USER_IDS, TICKET_IDS, TICKETS_DATA, SEAT_IDS, RESERVATION_IDS

REGISTER_URL = f"{BASE_URL}/auth/register"
LOGIN_URL = f"{BASE_URL}/auth/login"
TICKETS_URL = f"{BASE_URL}/ticket"
USER_TICKETS_URL = f"{BASE_URL}/ticket/my"
ADMIN_TICKETS_URL = f"{BASE_URL}/admin/tickets"
RESERVATIONS_URL = f"{BASE_URL}/reservations"


class TestTicketsAPI:
    def setup_method(self):
        self.admin_session = requests.Session()
        self.user1_session = requests.Session()
        self.user2_session = requests.Session()
        
        self.admin_user = next((user for user in USERS_DATA if user["email"] == "admin@example.com"), None)
        self.user1 = next((user for user in USERS_DATA if user["email"] == "user1@example.com"), None)
        self.user2 = next((user for user in USERS_DATA if user["email"] == "user2@example.com"), None)
        
        self.now = datetime.now()
        self.tomorrow = self.now + timedelta(days=1)
        
        self.ticket_data = {
            "theme": "failure",
            "message": "Тестовый тикет - проблема с компьютером"
        }
        
        self.reservation_ticket_data = {
            "theme": "other",
            "message": "Тестовый тикет по бронированию"
        }
        
        self.updated_status = {
            "status": "closed"
        }
        
        self.reservation_data = {
            "user_id": str(USER_IDS["user1"]),
            "seat_id": str(SEAT_IDS["seat1"]),
            "start": self.tomorrow.replace(hour=10, minute=0).isoformat(),
            "end": self.tomorrow.replace(hour=18, minute=0).isoformat()
        }
        
        self._cancel_all_user_reservations()

    def teardown_method(self):
        self.admin_session.close()
        self.user1_session.close()
        self.user2_session.close()

    def login_as_admin(self):
        admin_login = {
            "email": self.admin_user["email"],
            "password": self.admin_user["password"]
        }
        login_response = self.admin_session.post(LOGIN_URL, json=admin_login)
        assert login_response.status_code == 200, f"Не удалось войти как админ: {login_response.text}"
        return self.admin_session

    def login_as_user1(self):
        user_login = {
            "email": self.user1["email"],
            "password": self.user1["password"]
        }
        login_response = self.user1_session.post(LOGIN_URL, json=user_login)
        assert login_response.status_code == 200, f"Не удалось войти как пользователь 1: {login_response.text}"
        return self.user1_session

    def login_as_user2(self):
        user_login = {
            "email": self.user2["email"],
            "password": self.user2["password"]
        }
        login_response = self.user2_session.post(LOGIN_URL, json=user_login)
        assert login_response.status_code == 200, f"Не удалось войти как пользователь 2: {login_response.text}"
        return self.user2_session

    def _create_test_reservation(self):
        user_session = self.login_as_user1()
        response = user_session.post(RESERVATIONS_URL, json=self.reservation_data)
        assert response.status_code == 201, f"Не удалось создать бронирование: {response.text}"
        reservation_data = response.json()
        return reservation_data["id"]
    
    def _cancel_all_user_reservations(self):
        user_session = self.login_as_user1()
        response = user_session.get(RESERVATIONS_URL)
        if response.status_code == 200:
            reservations = response.json()
            for reservation in reservations:
                if reservation["status"] in ["future", "active"]:
                    cancel_response = user_session.patch(
                        f"{RESERVATIONS_URL}/{reservation['id']}",
                        json={"status": "closed"}
                    )
                    assert cancel_response.status_code == 200, f"Не удалось отменить бронирование: {cancel_response.text}"

    def test_create_ticket(self):
        user_session = self.login_as_user1()
        
        response = user_session.post(TICKETS_URL, json=self.ticket_data)
        
        assert response.status_code == 200, f"Код ответа {response.status_code}, ожидался 200. Ответ: {response.text}"
        
        data = response.json()
        assert data["theme"] == self.ticket_data["theme"]
        assert data["message"] == self.ticket_data["message"]
        assert "id" in data
        assert data["user_id"] == str(USER_IDS["user1"])
        assert data["status"] == "active"
        assert "made_on" in data
        
        return data["id"]

    def test_create_ticket_with_reservation(self):
        user_session = self.login_as_user1()
        
        reservation_id = self._create_test_reservation()
        
        reservation_ticket = {
            "theme": "other",
            "message": "Тестовый тикет по бронированию",
            "reservation_id": reservation_id
        }
        
        response = user_session.post(TICKETS_URL, json=reservation_ticket)
        
        assert response.status_code == 200, f"Код ответа {response.status_code}, ожидался 200. Ответ: {response.text}"
        
        data = response.json()
        assert data["theme"] == reservation_ticket["theme"]
        assert data["message"] == reservation_ticket["message"]
        assert data["reservation_id"] == reservation_id
        
        return data["id"]
    
    def test_create_ticket_wish_theme(self):
        user_session = self.login_as_user1()
        
        wish_ticket = {
            "theme": "wish",
            "message": "Пожелание по улучшению рабочего места"
        }
        
        response = user_session.post(TICKETS_URL, json=wish_ticket)
        
        assert response.status_code == 200, f"Код ответа {response.status_code}, ожидался 200. Ответ: {response.text}"
        
        data = response.json()
        assert data["theme"] == "wish"
        assert data["message"] == wish_ticket["message"]
        
        return data["id"]

    def test_get_user_tickets(self):
        user_session = self.login_as_user1()
    
        self.test_create_ticket()
        
        response = user_session.get(USER_TICKETS_URL)
        
        assert response.status_code == 200, f"Код ответа {response.status_code}, ожидался 200. Ответ: {response.text}"
        
        data = response.json()
        assert isinstance(data, list) or isinstance(data, dict), f"Ответ должен быть списком или словарем, получено: {type(data)}"
        
        if isinstance(data, list):
            assert len(data) > 0, "Ожидался непустой список тикетов"
            first_ticket = data[0]
        else:
            first_ticket = data
        
        assert "id" in first_ticket
        assert "user_id" in first_ticket
        assert "theme" in first_ticket
        assert "message" in first_ticket
        assert first_ticket["user_id"] == str(USER_IDS["user1"])

    def test_admin_get_all_tickets(self):
        user1_session = self.login_as_user1()
        user1_ticket_data = {
            "theme": "failure",
            "message": "Тикет от пользователя 1"
        }
        user1_response = user1_session.post(TICKETS_URL, json=user1_ticket_data)
        assert user1_response.status_code == 200
        
        user2_session = self.login_as_user2()
        user2_ticket_data = {
            "theme": "other",
            "message": "Тикет от пользователя 2"
        }
        user2_response = user2_session.post(TICKETS_URL, json=user2_ticket_data)
        assert user2_response.status_code == 200
        
        admin_session = self.login_as_admin()
        response = admin_session.get(ADMIN_TICKETS_URL)
        
        assert response.status_code == 200, f"Код ответа {response.status_code}, ожидался 200. Ответ: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2, "Должно быть как минимум 2 тикета"
        
        user1_tickets = [ticket for ticket in data if ticket["user_id"] == str(USER_IDS["user1"])]
        user2_tickets = [ticket for ticket in data if ticket["user_id"] == str(USER_IDS["user2"])]
        
        assert len(user1_tickets) > 0, "Должен быть хотя бы один тикет от пользователя 1"
        assert len(user2_tickets) > 0, "Должен быть хотя бы один тикет от пользователя 2"

    def test_admin_update_ticket_status(self):
        user_session = self.login_as_user1()
        create_response = user_session.post(TICKETS_URL, json=self.ticket_data)
        assert create_response.status_code == 200
        ticket_id = create_response.json()["id"]
        
        admin_session = self.login_as_admin()
        update_url = f"{BASE_URL}/admin/ticket/{ticket_id}/status"
        update_response = admin_session.patch(update_url, json=self.updated_status)
        
        assert update_response.status_code == 200, f"Код ответа {update_response.status_code}, ожидался 200. Ответ: {update_response.text}"
        
        data = update_response.json()
        assert data["status"] == self.updated_status["status"]
        
        admin_response = admin_session.get(ADMIN_TICKETS_URL)
        admin_data = admin_response.json()
        
        updated_ticket = next((ticket for ticket in admin_data if ticket["id"] == ticket_id), None)
        assert updated_ticket is not None, "Тикет не найден после обновления"
        assert updated_ticket["status"] == "closed", "Статус тикета не обновился на 'closed'"

    def test_user_cannot_update_ticket_status(self):
        user1_session = self.login_as_user1()
        create_response = user1_session.post(TICKETS_URL, json=self.ticket_data)
        assert create_response.status_code == 200
        ticket_id = create_response.json()["id"]
        

        update_url = f"{BASE_URL}/admin/ticket/{ticket_id}/status"
        update_response = user1_session.patch(update_url, json=self.updated_status)
        
        assert update_response.status_code in [401, 403], f"Код ответа {update_response.status_code}, ожидался 401 или 403. Ответ: {update_response.text}"

    def test_user_cannot_see_others_tickets(self):
        user1_session = self.login_as_user1()
        user1_ticket_data = {
            "theme": "failure",
            "message": "Тикет от пользователя 1"
        }
        user1_response = user1_session.post(TICKETS_URL, json=user1_ticket_data)
        assert user1_response.status_code == 200
        user1_ticket_id = user1_response.json()["id"]
        
        user2_session = self.login_as_user2()
        response = user2_session.get(USER_TICKETS_URL)
        
        assert response.status_code == 200, f"Код ответа {response.status_code}, ожидался 200. Ответ: {response.text}"
        
        data = response.json()
        if isinstance(data, list):
            user1_tickets_seen_by_user2 = [ticket for ticket in data if ticket.get("id") == user1_ticket_id]
            assert len(user1_tickets_seen_by_user2) == 0, "Пользователь 2 не должен видеть тикеты пользователя 1"
        elif isinstance(data, dict) and "id" in data:
            assert data["id"] != user1_ticket_id, "Пользователь 2 не должен видеть тикеты пользователя 1"

    def test_create_ticket_invalid_theme(self):
        user_session = self.login_as_user1()
        
        invalid_ticket = {
            "theme": "invalid_theme",
            "message": "Тикет с неверной темой"
        }
        
        response = user_session.post(TICKETS_URL, json=invalid_ticket)
        
        assert response.status_code == 422, f"Код ответа {response.status_code}, ожидался 422. Ответ: {response.text}"
