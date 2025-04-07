import pytest
import requests
import uuid
from data import BASE_URL, ADMIN_KEY, USERS_DATA, USER_IDS

REGISTER_URL = f"{BASE_URL}/auth/register"
LOGIN_URL = f"{BASE_URL}/auth/login"
ME_URL = f"{BASE_URL}/user/me"
UPDATE_URL = f"{BASE_URL}/user"

ACTUAL_USER_IDS = {}

class TestUserAPI:
    def setup_method(self):
        self.session = requests.Session()
        self.register_all_predefined_users()
        self.existing_user = USERS_DATA[1]
        self.random_email = f"test_{uuid.uuid4()}@example.com"
        self.random_password = f"random_pass_{uuid.uuid4()}"[:16]
        self.test_user = {"email": self.existing_user["email"], "password": self.existing_user["password"], "first_name": self.existing_user["first_name"]}
        self.new_test_user = {"email": self.random_email, "password": "password12345", "first_name": "Новый Тестовый Пользователь"}
        self.debug = False

    def register_all_predefined_users(self):
        session = requests.Session()
        for user_data in USERS_DATA:
            register_payload = {"email": user_data["email"], "password": user_data["password"], "first_name": user_data["first_name"]}
            if "role" in user_data and user_data["role"] == "admin":
                register_payload["role"] = "admin"
                register_payload["admin_key"] = ADMIN_KEY
            response = session.post(REGISTER_URL, json=register_payload)
        session.close()

    def teardown_method(self):
        self.session.close()

    def test_register_success(self):
        response = self.session.post(REGISTER_URL, json=self.new_test_user)
        assert response.status_code == 200, f"Код ответа {response.status_code}, ожидался 200. Ответ: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data
        assert data["user"]["email"] == self.new_test_user["email"]
        assert data["user"]["first_name"] == self.new_test_user["first_name"]
        assert "id" in data["user"]
        assert "password" not in data["user"]
        assert "access_token" in self.session.cookies
        assert "refresh_token" in self.session.cookies

    def test_register_predefined_users(self):
        global ACTUAL_USER_IDS
        for user_data in USERS_DATA:
            register_payload = {"email": user_data["email"], "password": user_data["password"], "first_name": user_data["first_name"]}
            if "role" in user_data and user_data["role"] == "admin":
                register_payload["role"] = "admin"
                register_payload["admin_key"] = ADMIN_KEY
            login_data = {"email": user_data["email"], "password": user_data["password"]}
            login_session = requests.Session()
            login_response = login_session.post(LOGIN_URL, json=login_data)
            assert login_response.status_code == 200, f"Логин для {user_data['email']} не удался: {login_response.text}"
            login_data = login_response.json()
            assert login_data["user"]["email"] == user_data["email"]
            assert login_data["user"]["first_name"] == user_data["first_name"]
            actual_id = login_data["user"]["id"]
            for key, value in USER_IDS.items():
                if user_data["id"] == value:
                    ACTUAL_USER_IDS[key] = uuid.UUID(actual_id)
                    break
            login_session.close()
        self._update_user_ids_in_data()

    def _update_user_ids_in_data(self):
        global USER_IDS
        for key, value in ACTUAL_USER_IDS.items():
            USER_IDS[key] = value

    def test_register_duplicate_email(self):
        duplicate_user = {"email": self.test_user["email"], "password": "different_pass123", "first_name": "Другое Имя"}
        response = self.session.post(REGISTER_URL, json=duplicate_user)
        assert response.status_code == 400
        assert "Пользователь с таким email уже существует" in response.text

    def test_login_success(self):
        for user_data in USERS_DATA:
            login_data = {"email": user_data["email"], "password": user_data["password"]}
            login_session = requests.Session()
            response = login_session.post(LOGIN_URL, json=login_data)
            assert response.status_code == 200, f"Логин для {user_data['email']} не удался: {response.text}"
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert "user" in data
            assert data["user"]["email"] == user_data["email"]
            login_session.close()

    def test_login_wrong_email(self):
        login_data = {"email": f"wrong_{uuid.uuid4()}@example.com", "password": self.existing_user["password"]}
        response = self.session.post(LOGIN_URL, json=login_data)
        assert response.status_code == 400
        assert "Неверный email" in response.text

    def test_login_wrong_password(self):
        login_data = {"email": self.test_user["email"], "password": f"wrong_password_{uuid.uuid4()}"[:16]}
        response = self.session.post(LOGIN_URL, json=login_data)
        assert response.status_code == 400
        assert "Неверный пароль" in response.text

    def test_me_authenticated(self):
        for user_data in USERS_DATA:
            login_data = {"email": user_data["email"], "password": user_data["password"]}
            auth_session = requests.Session()
            login_response = auth_session.post(LOGIN_URL, json=login_data)
            assert login_response.status_code == 200, f"Логин для {user_data['email']} не удался: {login_response.text}"
            response_data = login_response.json()
            access_token = response_data.get("access_token")
            assert access_token
            auth_session.headers.update({"Authorization": f"Bearer {access_token}"})
            response = auth_session.get(ME_URL)
            assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
            data = response.json()
            assert data["email"] == user_data["email"]
            assert data["first_name"] == user_data["first_name"]
            assert "id" in data
            assert "password" not in data
            assert "role" in data
            auth_session.close()

    def test_me_unauthenticated(self):
        session = requests.Session()
        response = session.get(ME_URL)
        assert response.status_code == 401
        session.close()

    def test_password_too_short(self):
        invalid_user = {"email": self.random_email, "password": "short", "first_name": "Тест Пользователь"}
        response = self.session.post(REGISTER_URL, json=invalid_user)
        assert response.status_code == 422
        data = response.json()
        assert "password" in str(data)

    def test_invalid_email_format(self):
        invalid_user = {"email": "invalid_email", "password": self.random_password, "first_name": "Тест Пользователь"}
        response = self.session.post(REGISTER_URL, json=invalid_user)
        assert response.status_code == 422
        data = response.json()
        assert "email" in str(data)

    def test_update_profile(self):
        user_data = USERS_DATA[1]
        login_data = {"email": user_data["email"], "password": user_data["password"]}
        auth_session = requests.Session()
        login_response = auth_session.post(LOGIN_URL, json=login_data)
        assert login_response.status_code == 200, f"Логин не удался: {login_response.text}"
        response_data = login_response.json()
        access_token = response_data.get("access_token")
        assert access_token
        auth_session.headers.update({"Authorization": f"Bearer {access_token}"})
        update_data = {"first_name": f"Обновленное Имя {uuid.uuid4()}"[:20]}
        update_response = auth_session.patch(UPDATE_URL, json=update_data)
        assert update_response.status_code == 200, f"Update failed with status {update_response.status_code}: {update_response.text}"
        response = auth_session.get(ME_URL)
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == update_data["first_name"]
        assert data["email"] == user_data["email"]
        auth_session.close()

