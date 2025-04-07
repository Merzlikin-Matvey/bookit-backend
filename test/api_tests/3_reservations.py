import pytest
import requests
import uuid
from datetime import datetime, timedelta
from data import BASE_URL, ADMIN_KEY, USERS_DATA, USER_IDS, SEATS_DATA, SEAT_IDS, RESERVATIONS_DATA, RESERVATION_IDS 

REGISTER_URL = f"{BASE_URL}/auth/register"
LOGIN_URL = f"{BASE_URL}/auth/login"
RESERVATIONS_URL = f"{BASE_URL}/reservations"
ACTIVE_RESERVATION_URL = f"{BASE_URL}/reservations/active"
ADMIN_RESERVATIONS_URL = f"{BASE_URL}/admin/reservations"
ADMIN_RESERVATION_CREATE_URL = f"{BASE_URL}/admin/reservation/create"
SEATS_URL = f"{BASE_URL}/seat"

class TestReservationsAPI:
    def setup_method(self):
        self._ensure_seats_exist()
        self.admin_session = requests.Session()
        self.user1_session = requests.Session()
        self.user2_session = requests.Session()
        self.admin_user = next((user for user in USERS_DATA if user["email"] == "admin@example.com"), None)
        self.user1 = next((user for user in USERS_DATA if user["email"] == "user1@example.com"), None)
        self.user2 = next((user for user in USERS_DATA if user["email"] == "user2@example.com"), None)
        self.now = datetime.now()
        self.tomorrow = self.now + timedelta(days=1)
        self.next_week = self.now + timedelta(days=7)
        self.user_reservation = {"user_id": str(USER_IDS["user1"]), "seat_id": str(SEAT_IDS["seat3"]),
                                 "start": self.tomorrow.replace(hour=10, minute=0).isoformat(),
                                 "end": self.tomorrow.replace(hour=18, minute=0).isoformat()}
        self.user_second_reservation = {"user_id": str(USER_IDS["user1"]), "seat_id": str(SEAT_IDS["seat4"]),
                                        "start": self.next_week.replace(hour=10, minute=0).isoformat(),
                                        "end": self.next_week.replace(hour=18, minute=0).isoformat()}
        self.admin_reservation = {"user_id": str(USER_IDS["user2"]), "seat_id": str(SEAT_IDS["seat4"]),
                                  "start": self.next_week.replace(hour=9, minute=0).isoformat(),
                                  "end": self.next_week.replace(hour=14, minute=0).isoformat()}
        self.updated_reservation = {"start": self.tomorrow.replace(hour=12, minute=0).isoformat(),
                                    "end": self.tomorrow.replace(hour=16, minute=0).isoformat()}
        self.cancelled_reservation = {"status": "closed"}
        self.overlapping_reservation = {"user_id": str(USER_IDS["user1"]), "seat_id": str(SEAT_IDS["seat3"]),
                                        "start": self.tomorrow.replace(hour=9, minute=0).isoformat(),
                                        "end": self.tomorrow.replace(hour=11, minute=0).isoformat()}

    def _ensure_seats_exist(self):
        try:
            admin_session = requests.Session()
            admin_login = {"email": "admin@example.com", "password": "adminpass1234"}
            login_response = admin_session.post(LOGIN_URL, json=admin_login)
            if login_response.status_code != 200:
                return
            check_response = admin_session.get(SEATS_URL, params={"start": datetime.now().isoformat(),
                                                                   "end": (datetime.now() + timedelta(days=1)).isoformat()})
            if check_response.status_code != 200 or len(check_response.json()) == 0:
                admin_session.close()
        except Exception as e:
            pass

    def teardown_method(self):
        self.admin_session.close()
        self.user1_session.close()
        self.user2_session.close()

    def login_as_admin(self):
        admin_login = {"email": self.admin_user["email"], "password": self.admin_user["password"]}
        login_response = self.admin_session.post(LOGIN_URL, json=admin_login)
        assert login_response.status_code == 200, f"Не удалось войти как админ: {login_response.text}"
        return self.admin_session

    def login_as_user1(self):
        user_login = {"email": self.user1["email"], "password": self.user1["password"]}
        login_response = self.user1_session.post(LOGIN_URL, json=user_login)
        assert login_response.status_code == 200, f"Не удалось войти как пользователь 1: {login_response.text}"
        return self.user1_session

    def login_as_user2(self):
        user_login = {"email": self.user2["email"], "password": self.user2["password"]}
        login_response = self.user2_session.post(LOGIN_URL, json=user_login)
        assert login_response.status_code == 200, f"Не удалось войти как пользователь 2: {login_response.text}"
        return self.user2_session

    def test_user_create_reservation(self):
        user_session = self.login_as_user1()
        self._cancel_all_user_reservations(user_session)
        response = user_session.post(RESERVATIONS_URL, json=self.user_reservation)
        assert response.status_code == 201, f"Код ответа {response.status_code}, ожидался 201. Ответ: {response.text}"
        data = response.json()
        assert data["user_id"] == str(USER_IDS["user1"])
        assert data["seat_id"] == self.user_reservation["seat_id"]
        assert "id" in data
        self.created_reservation_id = data["id"]
        return data["id"]

    def _cancel_all_user_reservations(self, session):
        response = session.get(RESERVATIONS_URL)
        if response.status_code == 200:
            reservations = response.json()
            for reservation in reservations:
                cancel_response = session.patch(f"{RESERVATIONS_URL}/{reservation['id']}", json={"status": "closed"})
                assert cancel_response.status_code == 200, f"Не удалось отменить бронирование: {cancel_response.text}"

    def test_user_cannot_create_multiple_active_reservations(self):
        user_session = self.login_as_user1()
        self._cancel_all_user_reservations(user_session)
        response1 = user_session.post(RESERVATIONS_URL, json=self.user_reservation)
        assert response1.status_code == 201, f"Ожидался 201, получено {response1.status_code}: {response1.text}"
        response2 = user_session.post(RESERVATIONS_URL, json=self.user_second_reservation)
        assert response2.status_code == 400, f"Ожидался 400, получено {response2.status_code}: {response2.text}"
        assert ("active reservation" in response2.text.lower() or "активное бронирование" in response2.text.lower()), \
            "Сообщение об ошибке отсутствует или некорректно."

    def test_cancel_and_create_new_reservation(self):
        user_session = self.login_as_user1()
        self._cancel_all_user_reservations(user_session)
        response1 = user_session.post(RESERVATIONS_URL, json=self.user_reservation)
        assert response1.status_code == 201, f"Код ответа {response1.status_code}, ожидался 201. Ответ: {response1.text}"
        reservation_id = response1.json()["id"]
        response_error = user_session.post(RESERVATIONS_URL, json=self.user_second_reservation)
        assert response_error.status_code == 400, f"Код ответа {response_error.status_code}, ожидался 400. Ответ: {response_error.text}"
        cancel_response = user_session.patch(f"{RESERVATIONS_URL}/{reservation_id}", json=self.cancelled_reservation)
        assert cancel_response.status_code == 200, f"Код ответа {cancel_response.status_code}, ожидался 200. Ответ: {cancel_response.text}"
        get_response = user_session.get(f"{RESERVATIONS_URL}/{reservation_id}")
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["status"] == "closed", f"Статус бронирования должен быть 'closed', получено: {get_data['status']}"
        response2 = user_session.post(RESERVATIONS_URL, json=self.user_second_reservation)
        assert response2.status_code == 201, f"Код ответа {response2.status_code}, ожидался 201. Ответ: {response2.text}"
        data = response2.json()
        assert data["user_id"] == str(USER_IDS["user1"])
        assert data["seat_id"] == self.user_second_reservation["seat_id"]
        assert "id" in data
        assert data["id"] != reservation_id
        return data["id"]

    def test_admin_can_create_reservation_for_user(self):
        admin_session = self.login_as_admin()
        user2_session = self.login_as_user2()
        self._cancel_all_user_reservations(user2_session)
        response = admin_session.post(ADMIN_RESERVATION_CREATE_URL, json=self.admin_reservation)
        assert response.status_code == 201, f"Код ответа {response.status_code}, ожидался 201. Ответ: {response.text}"
        data = response.json()
        assert data["user_id"] == self.admin_reservation["user_id"]
        assert data["seat_id"] == self.admin_reservation["seat_id"]
        assert "id" in data
        second_reservation = {"user_id": str(USER_IDS["user2"]), "seat_id": str(SEAT_IDS["seat3"]),
                              "start": self.tomorrow.replace(hour=10, minute=0).isoformat(),
                              "end": self.tomorrow.replace(hour=18, minute=0).isoformat()}
        response2 = admin_session.post(ADMIN_RESERVATION_CREATE_URL, json=second_reservation)
        assert response2.status_code == 400, f"Код ответа {response2.status_code}, ожидался 400. Ответ: {response2.text}"
        return data["id"]

    def test_admin_can_create_after_canceling(self):
        admin_session = self.login_as_admin()
        user2_session = self.login_as_user2()
        self._cancel_all_user_reservations(user2_session)
        first_reservation = {"user_id": str(USER_IDS["user2"]), "seat_id": str(SEAT_IDS["seat3"]),
                             "start": self.tomorrow.replace(hour=10, minute=0).isoformat(),
                             "end": self.tomorrow.replace(hour=18, minute=0).isoformat()}
        response1 = admin_session.post(ADMIN_RESERVATION_CREATE_URL, json=first_reservation)
        assert response1.status_code == 201, f"Код ответа {response1.status_code}, ожидался 201. Ответ: {response1.text}"
        reservation_id = response1.json()["id"]
        cancel_response = admin_session.patch(f"{BASE_URL}/admin/reservation/{reservation_id}", json={"status": "closed"})
        assert cancel_response.status_code == 200, f"Не удалось отменить бронирование: {cancel_response.text}"
        second_reservation = {"user_id": str(USER_IDS["user2"]), "seat_id": str(SEAT_IDS["seat4"]),
                              "start": self.next_week.replace(hour=9, minute=0).isoformat(),
                              "end": self.next_week.replace(hour=14, minute=0).isoformat()}
        response2 = admin_session.post(ADMIN_RESERVATION_CREATE_URL, json=second_reservation)
        assert response2.status_code == 201, f"Код ответа {response2.status_code}, ожидался 201. Ответ: {response2.text}"

    def test_different_users_can_have_active_reservations(self):
        user1_session = self.login_as_user1()
        self._cancel_all_user_reservations(user1_session)
        user2_session = self.login_as_user2()
        self._cancel_all_user_reservations(user2_session)
        response1 = user1_session.post(RESERVATIONS_URL, json=self.user_reservation)
        assert response1.status_code == 201, f"Код ответа {response1.status_code}, ожидался 201. Ответ: {response1.text}"
        user2_reservation = {"user_id": str(USER_IDS["user2"]), "seat_id": str(SEAT_IDS["seat4"]),
                             "start": self.tomorrow.replace(hour=10, minute=0).isoformat(),
                             "end": self.tomorrow.replace(hour=18, minute=0).isoformat()}
        response2 = user2_session.post(RESERVATIONS_URL, json=user2_reservation)
        assert response2.status_code == 201, f"Код ответа {response2.status_code}, ожидался 201. Ответ: {response2.text}"

    def test_get_user_reservations(self):
        user_session = self.login_as_user1()
        self._cancel_all_user_reservations(user_session)
        response = user_session.post(RESERVATIONS_URL, json=self.user_reservation)
        assert response.status_code == 201, f"Код ответа {response.status_code}, ожидался 201. Ответ: {response.text}"
        get_response = user_session.get(RESERVATIONS_URL)
        assert get_response.status_code == 200, f"Код ответа {get_response.status_code}, ожидался 200. Ответ: {get_response.text}"
        data = get_response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "id" in data[0]
        assert "user_id" in data[0]
        assert "seat_id" in data[0]
        assert "start" in data[0]
        assert "end" in data[0]
        assert "status" in data[0]

    def test_get_reservation_by_id(self):
        user_session = self.login_as_user1()
        self._cancel_all_user_reservations(user_session)
        response = user_session.post(RESERVATIONS_URL, json=self.user_reservation)
        assert response.status_code == 201, f"Код ответа {response.status_code}, ожидался 201. Ответ: {response.text}"
        reservation_id = response.json()["id"]
        get_response = user_session.get(f"{RESERVATIONS_URL}/{reservation_id}")
        assert get_response.status_code == 200, f"Код ответа {get_response.status_code}, ожидался 200. Ответ: {get_response.text}"
        data = get_response.json()
        assert data["id"] == reservation_id
        assert data["user_id"] == str(USER_IDS["user1"])
        assert data["seat_id"] == self.user_reservation["seat_id"]

    def test_update_reservation(self):
        user_session = self.login_as_user1()
        self._cancel_all_user_reservations(user_session)
        response = user_session.post(RESERVATIONS_URL, json=self.user_reservation)
        assert response.status_code == 201, f"Код ответа {response.status_code}, ожидался 201. Ответ: {response.text}"
        reservation_id = response.json()["id"]
        update_response = user_session.patch(f"{RESERVATIONS_URL}/{reservation_id}", json=self.updated_reservation)
        assert update_response.status_code == 200, f"Код ответа {update_response.status_code}, ожидался 200. Ответ: {update_response.text}"
        data = update_response.json()
        assert self.updated_reservation["start"] in data["start"]
        assert self.updated_reservation["end"] in data["end"]
        get_response = user_session.get(f"{RESERVATIONS_URL}/{reservation_id}")
        get_data = get_response.json()
        assert self.updated_reservation["start"] in get_data["start"]
        assert self.updated_reservation["end"] in get_data["end"]

    def test_cancel_reservation(self):
        user_session = self.login_as_user1()
        self._cancel_all_user_reservations(user_session)
        response = user_session.post(RESERVATIONS_URL, json=self.user_reservation)
        assert response.status_code == 201, f"Код ответа {response.status_code}, ожидался 201. Ответ: {response.text}"
        reservation_id = response.json()["id"]
        cancel_response = user_session.patch(f"{RESERVATIONS_URL}/{reservation_id}", json=self.cancelled_reservation)
        assert cancel_response.status_code == 200, f"Код ответа {cancel_response.status_code}, ожидался 200. Ответ: {cancel_response.text}"
        data = cancel_response.json()
        assert data["status"] == self.cancelled_reservation["status"]
        get_response = user_session.get(f"{RESERVATIONS_URL}/{reservation_id}")
        get_data = get_response.json()
        assert get_data["status"] == self.cancelled_reservation["status"]

    def test_user_cannot_modify_others_reservation(self):
        user1_session = self.login_as_user1()
        self._cancel_all_user_reservations(user1_session)
        user2_session = self.login_as_user2()
        self._cancel_all_user_reservations(user2_session)
        response = user1_session.post(RESERVATIONS_URL, json=self.user_reservation)
        assert response.status_code == 201, f"Код ответа {response.status_code}, ожидался 201. Ответ: {response.text}"
        reservation_id = response.json()["id"]
        update_response = user2_session.patch(f"{RESERVATIONS_URL}/{reservation_id}", json=self.updated_reservation)
        assert update_response.status_code in [403, 404], f"Код ответа {update_response.status_code}, ожидался 403 или 404. Ответ: {update_response.text}"

    def test_admin_can_modify_any_reservation(self):
        user1_session = self.login_as_user1()
        self._cancel_all_user_reservations(user1_session)
        response = user1_session.post(RESERVATIONS_URL, json=self.user_reservation)
        assert response.status_code == 201, f"Код ответа {response.status_code}, ожидался 201. Ответ: {response.text}"
        reservation_id = response.json()["id"]
        admin_session = self.login_as_admin()
        admin_update = {"status": "did_not_come"}
        admin_response = admin_session.patch(f"{BASE_URL}/admin/reservation/{reservation_id}", json=admin_update)
        assert admin_response.status_code == 200, f"Код ответа {admin_response.status_code}, ожидался 200. Ответ: {admin_response.text}"
        data = admin_response.json()
        assert data["status"] == admin_update["status"]

    def test_admin_can_delete_reservation(self):
        user1_session = self.login_as_user1()
        self._cancel_all_user_reservations(user1_session)
        response = user1_session.post(RESERVATIONS_URL, json=self.user_reservation)
        assert response.status_code == 201, f"Код ответа {response.status_code}, ожидался 201. Ответ: {response.text}"
        reservation_id = response.json()["id"]
        admin_session = self.login_as_admin()
        delete_response = admin_session.delete(f"{BASE_URL}/admin/reservation/{reservation_id}")
        assert delete_response.status_code in [200, 204], f"Код ответа {delete_response.status_code}, ожидался 200 или 204. Ответ: {delete_response.text}"
        check_response = user1_session.get(f"{RESERVATIONS_URL}/{reservation_id}")
        assert check_response.status_code == 404, "Бронирование не было удалено"

    def test_get_active_reservation(self):
        user_session = self.login_as_user1()
        self._cancel_all_user_reservations(user_session)
        active_reservation = {"user_id": str(USER_IDS["user1"]), "seat_id": str(SEAT_IDS["seat3"]),
                              "start": (self.now - timedelta(hours=1)).isoformat(),
                              "end": (self.now + timedelta(hours=1)).isoformat()}
        create_response = user_session.post(RESERVATIONS_URL, json=active_reservation)
        assert create_response.status_code == 201, f"Код ответа {create_response.status_code}, ожидался 201. Ответ: {create_response.text}"
        response = user_session.get(ACTIVE_RESERVATION_URL)
        assert response.status_code == 200, f"Код ответа {response.status_code}, ожидался 200. Ответ: {response.text}"
        data = response.json()
        assert "id" in data
        assert "user_id" in data
        assert "seat_id" in data
        assert data["status"] in ["active", "future"]

    def test_admin_get_all_reservations(self):
        admin_session = self.login_as_admin()
        response = admin_session.get(ADMIN_RESERVATIONS_URL)
        assert response.status_code == 200, f"Код ответа {response.status_code}, ожидался 200. Ответ: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "id" in data[0]
            assert "user_id" in data[0]
            assert "seat_id" in data[0]
            assert "start" in data[0]
            assert "end" in data[0]
            assert "status" in data[0]