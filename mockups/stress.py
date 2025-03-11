import uuid
from datetime import datetime, timedelta
import httpx
import asyncio
import json

BASE_URL = "http://localhost:8080/api"
VERIFY_SSL = False

# Local definitions to send requests directly to the server:
async def register_user(user_data):
    async with httpx.AsyncClient(verify=VERIFY_SSL) as client:
        response = await client.post(f"{BASE_URL}/auth/register", json=user_data)
        if response.status_code in [200, 201]:
            return response.json()["user"], response.cookies
        else:
            print(f"User register failed for {user_data['email']}: {response.status_code}")
            return None, None

async def login_user(credentials):
    async with httpx.AsyncClient(verify=VERIFY_SSL) as client:
        response = await client.post(f"{BASE_URL}/auth/login", json=credentials)
        if response.status_code == 200:
            return response.json()["user"], response.cookies
        else:
            print(f"Login failed for {credentials['email']}: {response.status_code}")
            return None, None

async def create_seat(seat_data, user_info, cookies):
    async with httpx.AsyncClient(cookies=cookies, verify=VERIFY_SSL) as client:
        response = await client.post(f"{BASE_URL}/seat", json=seat_data)
        if response.status_code in [200, 201]:
            return response.json()
        else:
            print("Seat creation failed:", response.status_code)
            return None

async def create_reservation(reservation_data, user_cookies):
    async with httpx.AsyncClient(cookies=user_cookies, verify=VERIFY_SSL) as client:
        response = await client.post(f"{BASE_URL}/reservations", json=reservation_data)
        if response.status_code in [200, 201]:
            return response.json()
        else:
            print("Reservation failed:", response.status_code)
            return None

async def stress_test():
    admin_credentials = {"email": "admin@example.com", "password": "adminpass1234"}
    admin_user, admin_cookies = await login_user(admin_credentials)
    if not admin_cookies:
        print("Admin login failed.")
        return
    seat_data = {
        "name": "Stress Seat",
        "type": "desk",
        "x": 47.0,
        "y": -1.6,
        "width": 1.0,
        "has_computer": True,
        "has_water": True,
        "has_kitchen": False,
        "has_smart_desk": False,
        "is_quite": True,
        "is_talk_room": False,
        "is_available": True
    }
    seat = await create_seat(seat_data, admin_user, admin_cookies)
    if not seat:
        print("Seat creation failed.")
        return
    stress_seat_id = seat["id"]

    USERS_COUNT = 1000
    # Create 10k users and create a reservation on one of 1000 different days.
    for i in range(USERS_COUNT):
        user_data = {
            "email": f"stress_user_{i}@example.com",
            "first_name": "Stress",
            "password": "stresspass",
            "role": "user"
        }
        user, cookies = await register_user(user_data)
        if not (user and cookies):
            print(f"User creation failed for index {i}")
            continue


        day_offset = i % 1000
        reservation_day = datetime.now() + timedelta(days=day_offset)
        start_time = reservation_day.replace(hour=9, minute=0, second=0, microsecond=0)
        end_time = reservation_day.replace(hour=18, minute=0, second=0, microsecond=0)
        reservation_data = {
            "user_id": user["id"],
            "seat_id": stress_seat_id,
            "start": start_time.isoformat(),
            "end": end_time.isoformat()
        }
        await create_reservation(reservation_data, cookies)
        if i % 100 == 0:
            print(f"Created reservation for user {i}")

if __name__ == "__main__":
    asyncio.run(stress_test())


