import pytest
import requests
import uuid
from data import BASE_URL, ADMIN_KEY, USERS_DATA, USER_IDS, SEATS_DATA, SEAT_IDS
from datetime import datetime, timedelta

REGISTER_URL = f"{BASE_URL}/auth/register"
LOGIN_URL = f"{BASE_URL}/auth/login"
SEATS_URL = f"{BASE_URL}/seat"

ACTUAL_SEAT_IDS = {}

class TestSeatsAPI:
    def setup_method(self):
        self.admin_session = requests.Session()
        self.user_session = requests.Session()
        self.admin_data = {"email": "admin@example.com", "password": "adminpass1234", "first_name": "Admin", "role": "admin", "admin_key": ADMIN_KEY}
        admin_login = {"email": "admin@example.com", "password": "adminpass1234"}
        login_response = requests.post(LOGIN_URL, json=admin_login)
        if login_response.status_code != 200:
            requests.post(REGISTER_URL, json=self.admin_data)
        self.user_data = {"email": "user1@example.com", "password": "userpass1234", "first_name": "Test User"}
        user_login = {"email": "user1@example.com", "password": "userpass1234"}
        login_response = requests.post(LOGIN_URL, json=user_login)
        if login_response.status_code != 200:
            requests.post(REGISTER_URL, json=self.user_data)
        self.new_seat_data = {"name": f"Test Seat {uuid.uuid4()}", "type": "desk", "x": 50.0, "y": 50.0, "has_computer": True, "has_water": True, "has_kitchen": False, "has_smart_desk": True, "is_quite": False, "is_talk_room": False}
        self.updated_seat_data = {"x": 55.0, "y": 55.0, "has_water": False, "is_quite": True}
        self.now = datetime.now()
        self.start_time = self.now.isoformat()
        self.end_time = (self.now + timedelta(days=1)).isoformat()

    def teardown_method(self):
        self.admin_session.close()
        self.user_session.close()

    def login_as_admin(self):
        admin_login = {"email": "admin@example.com", "password": "adminpass1234"}
        login_response = self.admin_session.post(LOGIN_URL, json=admin_login)
        assert login_response.status_code == 200, f"Не удалось войти как админ: {login_response.text}"
        return self.admin_session

    def login_as_user(self):
        user_login = {"email": "user1@example.com", "password": "userpass1234"}
        login_response = self.user_session.post(LOGIN_URL, json=user_login)
        assert login_response.status_code == 200, f"Не удалось войти как пользователь: {login_response.text}"
        return self.user_session

    def test_admin_create_seat(self):
        admin_session = self.login_as_admin()
        response = admin_session.post(SEATS_URL, json=self.new_seat_data)
        assert response.status_code == 200, f"Код ответа {response.status_code}, ожидался 200. Ответ: {response.text}"
        data = response.json()
        assert data["x"] == self.new_seat_data["x"]
        assert data["y"] == self.new_seat_data["y"]
        assert data["name"] == self.new_seat_data["name"]
        assert data["type"] == self.new_seat_data["type"]
        assert data["has_computer"] == self.new_seat_data["has_computer"]
        assert data["has_water"] == self.new_seat_data["has_water"]
        assert "id" in data
        self.created_seat_id = data["id"]
        return data["id"]

    def test_create_all_predefined_seats(self):
        global ACTUAL_SEAT_IDS
        admin_session = self.login_as_admin()
        for key, seat_id in SEAT_IDS.items():
            seat_data = next((seat for seat in SEATS_DATA if seat["id"] == seat_id), None)
            if seat_data:
                create_data = {"name": f"Seat {key}", "type": "desk", "x": seat_data["x"], "y": seat_data["y"], "has_computer": seat_data["has_computer"], "has_water": seat_data["has_water"], "has_kitchen": seat_data["has_kitchen"], "has_smart_desk": seat_data["has_smart_desk"], "is_quite": seat_data["is_quite"], "is_talk_room": seat_data["is_talk_room"]}
                response = admin_session.post(SEATS_URL, json=create_data)
                assert response.status_code == 200, f"Не удалось создать место {key}: {response.text}"
                actual_id = response.json()["id"]
                ACTUAL_SEAT_IDS[key] = uuid.UUID(actual_id)
        self._update_seat_ids_in_data()

    def _update_seat_ids_in_data(self):
        global SEAT_IDS
        for key, value in ACTUAL_SEAT_IDS.items():
            SEAT_IDS[key] = value

    def test_regular_user_cannot_create_seat(self):
        user_session = self.login_as_user()
        response = user_session.post(SEATS_URL, json=self.new_seat_data)
        assert response.status_code == 403, f"Код ответа {response.status_code}, ожидался 403. Ответ: {response.text}"

    def test_get_all_seats(self):
        params = {"start": self.start_time, "end": self.end_time}
        admin_session = self.login_as_admin()
        admin_response = admin_session.get(SEATS_URL, params=params)
        assert admin_response.status_code == 200, f"Код ответа {admin_response.status_code}, ожидался 200. Ответ: {admin_response.text}"
        admin_data = admin_response.json()
        assert isinstance(admin_data, list)
        if len(admin_data) > 0:
            assert "id" in admin_data[0]
            assert "x" in admin_data[0]
            assert "y" in admin_data[0]
        user_session = self.login_as_user()
        user_response = user_session.get(SEATS_URL, params=params)
        assert user_response.status_code == 200
        user_data = user_response.json()
        assert isinstance(user_data, list)
        if len(user_data) > 0:
            assert "id" in user_data[0]
            assert "x" in user_data[0]
            assert "y" in user_data[0]
        assert len(admin_data) == len(user_data)

    def test_get_seat_by_id(self):
        admin_session = self.login_as_admin()
        seat_id = self.test_admin_create_seat()
        admin_session = self.login_as_admin()
        admin_response = admin_session.get(f"{SEATS_URL}/{seat_id}")
        assert admin_response.status_code == 200, f"Код ответа {admin_response.status_code}, ожидался 200. Ответ: {admin_response.text}"
        admin_data = admin_response.json()
        assert admin_data["id"] == seat_id
        user_session = self.login_as_user()
        user_response = user_session.get(f"{SEATS_URL}/{seat_id}")
        assert user_response.status_code == 200
        user_data = user_response.json()
        assert user_data["id"] == seat_id

    def test_admin_update_seat(self):
        admin_session = self.login_as_admin()
        seat_id = self.test_admin_create_seat()
        admin_session = self.login_as_admin()
        response = admin_session.patch(f"{SEATS_URL}/{seat_id}", json=self.updated_seat_data)
        assert response.status_code == 200, f"Код ответа {response.status_code}, ожидался 200. Ответ: {response.text}"
        data = response.json()
        assert data["x"] == self.updated_seat_data["x"]
        assert data["y"] == self.updated_seat_data["y"]
        assert data["has_water"] == self.updated_seat_data["has_water"]
        assert data["is_quite"] == self.updated_seat_data["is_quite"]

    def test_regular_user_cannot_update_seat(self):
        admin_session = self.login_as_admin()
        seat_id = self.test_admin_create_seat()
        user_session = self.login_as_user()
        response = user_session.patch(f"{SEATS_URL}/{seat_id}", json=self.updated_seat_data)
        assert response.status_code == 403, f"Код ответа {response.status_code}, ожидался 403. Ответ: {response.text}"

    def test_admin_delete_seat(self):
        admin_session = self.login_as_admin()
        seat_id = self.test_admin_create_seat()
        admin_session = self.login_as_admin()
        response = admin_session.delete(f"{SEATS_URL}/{seat_id}")
        assert response.status_code == 204, f"Код ответа {response.status_code}, ожидался 200. Ответ: {response.text}"
        admin_session = self.login_as_admin()
        get_response = admin_session.get(f"{SEATS_URL}/{seat_id}")
        assert get_response.status_code == 404

    def test_regular_user_cannot_delete_seat(self):
        admin_session = self.login_as_admin()
        seat_id = self.test_admin_create_seat()
        user_session = self.login_as_user()
        response = user_session.delete(f"{SEATS_URL}/{seat_id}")
        assert response.status_code == 403, f"Код ответа {response.status_code}, ожидался 403. Ответ: {response.text}"
        admin_session = self.login_as_admin()
        admin_get_response = admin_session.get(f"{SEATS_URL}/{seat_id}")
        assert admin_get_response.status_code == 200

    def test_invalid_seat_data(self):
        admin_session = self.login_as_admin()
        invalid_data = {"x": "не число", "y": 10.0}
        response = admin_session.post(SEATS_URL, json=invalid_data)
        assert response.status_code == 422, f"Код ответа {response.status_code}, ожидался 422. Ответ: {response.text}"
