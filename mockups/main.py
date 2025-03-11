import uuid
from datetime import datetime, timedelta
import httpx
import asyncio
import json

#BASE_URL = "https://prod-team-17-61ojpp1i.final.prodcontest.ru/api"
BASE_URL = "http://localhost:8080/api"

ADMIN_KEY = "j3h4m1dm4mpk6"

VERIFY_SSL = False

GENERATED_USER_IDS = {}
GENERATED_SEAT_IDS = {}
GENERATED_RESERVATION_IDS = {}
GENERATED_TICKET_IDS = {}

USERS_DATA = [
    {
        "email": "admin@example.com",
        "first_name": "Admin",
        "role": "admin",
        "password": "adminpass1234"
    },
    {
        "email": "user1@example.com",
        "first_name": "Test User",
        "role": "user",
        "password": "userpass1234"
    },
    {
        "email": "user2@example.com",
        "first_name": "Another User",
        "role": "user",
        "password": "password1234"
    },
    {
        "email": "manager@example.com",
        "first_name": "Office Manager",
        "role": "user",
        "password": "manager1234"
    }
]



SEATS_DATA = [
    {
        "name": "Рабочее место 1",
        "type": "desk",
        "x": 47.483,
        "y": -1.69,
        "width": 1.0,
        "has_computer": True,
        "has_water": True,
        "has_kitchen": False,
        "has_smart_desk": True,
        "is_quite": False,
        "is_talk_room": False,
        "is_available": True
    },
{
        "name": "Рабочее место 2",
        "type": "desk",
        "x": 47.483,
        "y": -1.53,
        "width": 1.0,
        "has_computer": True,
        "has_water": True,
        "has_kitchen": False,
        "has_smart_desk": True,
        "is_quite": False,
        "is_talk_room": False,
        "is_available": True
    },
]

today = datetime.now()
tomorrow = today + timedelta(days=1)
next_week = today + timedelta(days=7)

RESERVATION_TEMPLATES = [
    {
        "user_key": "user1",
        "seat_key": "seat1",
        "start_time": today.replace(hour=9, minute=0, second=0, microsecond=0),
        "end_time": today.replace(hour=18, minute=0, second=0, microsecond=0),
    },
    {
        "user_key": "user2",
        "seat_key": "seat2",
        "start_time": tomorrow.replace(hour=10, minute=0, second=0, microsecond=0),
        "end_time": tomorrow.replace(hour=16, minute=0, second=0, microsecond=0),
    },
    {
        "user_key": "manager",
        "seat_key": "meeting_room",
        "start_time": tomorrow.replace(hour=14, minute=0, second=0, microsecond=0),
        "end_time": tomorrow.replace(hour=16, minute=0, second=0, microsecond=0),
    },
    {
        "user_key": "user1",
        "seat_key": "quiet_zone",
        "start_time": next_week.replace(hour=9, minute=0, second=0, microsecond=0),
        "end_time": next_week.replace(hour=18, minute=0, second=0, microsecond=0),
    }
]


TICKET_TEMPLATES = [
    {
        "user_key": "user1",
        "reservation_index": 0,
        "seat_key": "seat1",
        "theme": "failure",
        "message": "Не работает монитор на рабочем месте",
        "made_on": today - timedelta(hours=3)
    },
    {
        "user_key": "user2",
        "reservation_index": 1,
        "seat_key": "seat2",
        "theme": "wish",
        "message": "Требуется доступ к переговорной комнате",
        "made_on": today - timedelta(days=1)
    }
]

async def register_user(user_data):
    """Register a user and return user data with server-generated ID"""
    try:
        async with httpx.AsyncClient(verify=VERIFY_SSL) as client:
            response = await client.post(
                f"{BASE_URL}/auth/register",
                json={
                    "email": user_data["email"],
                    "first_name": user_data["first_name"],
                    "password": user_data["password"],
                    "role": user_data["role"],
                    "admin_key": ADMIN_KEY if user_data["role"] == "admin" else None
                }
            )
            if response.status_code == 200 or response.status_code == 201:
                user_response = response.json()
                if "user" in user_response:
                    user_id = user_response["user"]["id"]
                    user_key = user_data["email"].split("@")[0]
                    GENERATED_USER_IDS[user_key] = user_id
                    print(f"Successfully registered user: {user_data['email']} with ID: {user_id}")
                    return user_response["user"], response.cookies
                else:
                    print(f"User data not found in response: {user_response}")
                    return None, None
            else:
                print(f"Failed to register user {user_data['email']}: {response.status_code}, {response.text}")
                return await login_user(user_data)
    except Exception as e:
        print(f"Error registering user {user_data['email']}: {str(e)}")
        return None, None

async def login_user(user_data):
    """Login a user and return user data with ID"""
    try:
        async with httpx.AsyncClient(verify=VERIFY_SSL) as client:
            response = await client.post(
                f"{BASE_URL}/auth/login",
                json={
                    "email": user_data["email"],
                    "password": user_data["password"]
                }
            )
            if response.status_code == 200:
                user_response = response.json()
                if "user" in user_response:
                    user_id = user_response["user"]["id"]
                    user_key = user_data["email"].split("@")[0]
                    GENERATED_USER_IDS[user_key] = user_id
                    print(f"Successfully logged in user: {user_data['email']} with ID: {user_id}")
                    return user_response["user"], response.cookies
                else:
                    print(f"User data not found in response: {user_response}")
                    return None, None
            else:
                print(f"Failed to login user {user_data['email']}: {response.status_code}, {response.text}")
                return None, None
    except Exception as e:
        print(f"Error logging in user {user_data['email']}: {str(e)}")
        return None, None

async def create_seat(seat_data, user_info, cookies):
    """Create a seat and return seat data with server-generated ID"""
    try:
        async with httpx.AsyncClient(cookies=cookies, verify=VERIFY_SSL) as client:
            response = await client.post(
                f"{BASE_URL}/seat",
                json=seat_data
            )
            if response.status_code == 200 or response.status_code == 201:
                created_seat = response.json()
                seat_id = created_seat["id"]
                seat_index = SEATS_DATA.index(seat_data)
                
                if seat_index == 0:
                    seat_key = "seat1"
                elif seat_index == 1:
                    seat_key = "seat2"
                elif seat_index == 2:
                    seat_key = "seat3"
                elif seat_index == 3:
                    seat_key = "seat4"
                elif seat_index == 4:
                    seat_key = "meeting_room"
                elif seat_index == 5:
                    seat_key = "quiet_zone"
                else:
                    seat_key = f"seat_{seat_index}"
                
                GENERATED_SEAT_IDS[seat_key] = seat_id
                print(f"Successfully created seat '{seat_data['name']}' with ID: {seat_id}")
                return created_seat
            else:
                print(f"Failed to create seat: {response.status_code}, {response.text}")
                return None
    except Exception as e:
        print(f"Error creating seat: {str(e)}")
        return None

async def create_reservation(reservation_data, user_cookies):
    """Create a reservation and return reservation data with server-generated ID"""
    try:
        async with httpx.AsyncClient(cookies=user_cookies, verify=VERIFY_SSL) as client:
            response = await client.post(
                f"{BASE_URL}/reservations",
                json=reservation_data
            )
            if response.status_code == 200 or response.status_code == 201:
                created_reservation = response.json()
                reservation_id = created_reservation["id"]
                GENERATED_RESERVATION_IDS[len(GENERATED_RESERVATION_IDS)] = reservation_id
                print(f"Successfully created reservation with ID: {reservation_id}")
                return created_reservation
            else:
                print(f"Failed to create reservation: {response.status_code}, {response.text}")
                return None
    except Exception as e:
        print(f"Error creating reservation: {str(e)}")
        return None

async def create_ticket(ticket_data, user_cookies):
    """Create a ticket and return ticket data with server-generated ID"""
    try:
        async with httpx.AsyncClient(cookies=user_cookies, verify=VERIFY_SSL) as client:
            response = await client.post(
                f"{BASE_URL}/ticket",
                json=ticket_data
            )
            if response.status_code == 200 or response.status_code == 201:
                created_ticket = response.json()
                ticket_id = created_ticket["id"]
                GENERATED_TICKET_IDS[len(GENERATED_TICKET_IDS)] = ticket_id
                print(f"Successfully created ticket with ID: {ticket_id}")
                return created_ticket
            else:
                print(f"Failed to create ticket: {response.status_code}, {response.text}")
                return None
    except Exception as e:
        print(f"Error creating ticket: {str(e)}")
        return None

async def main():
    print("Starting mockup data creation with server-generated IDs...")

    user_cookies = {}

    for user_data in USERS_DATA:
        user_info, cookies = await register_user(user_data)
        if user_info and cookies:
            user_key = user_data["email"].split("@")[0]
            user_cookies[user_key] = cookies
    

    admin_cookies = user_cookies.get("admin")
    if not admin_cookies:
        print("Admin user not registered. Cannot create seats.")
        return
    
    admin_info = None
    for user in USERS_DATA:
        if user["email"] == "admin@example.com":
            admin_info = user
            break

    for seat_data in SEATS_DATA:
        await create_seat(seat_data, admin_info, admin_cookies)

    created_reservations = []
    for i, template in enumerate(RESERVATION_TEMPLATES):
        user_key = template["user_key"]
        seat_key = template["seat_key"]
        
        if user_key not in GENERATED_USER_IDS or seat_key not in GENERATED_SEAT_IDS:
            print(f"Missing user or seat ID for reservation {i}, skipping")
            continue
        
        reservation_data = {
            "user_id": GENERATED_USER_IDS[user_key],
            "seat_id": GENERATED_SEAT_IDS[seat_key],
            "start": template["start_time"].isoformat(),
            "end": template["end_time"].isoformat(),
        }
        
        reservation = await create_reservation(reservation_data, user_cookies[user_key])
        if reservation:
            created_reservations.append(reservation)

    for template in TICKET_TEMPLATES:
        user_key = template["user_key"]
        seat_key = template["seat_key"]
        res_index = template["reservation_index"]
        
        if user_key not in user_cookies or res_index >= len(created_reservations) or seat_key not in GENERATED_SEAT_IDS:
            print(f"Missing data for ticket creation, skipping")
            continue
        
        ticket_data = {
            "reservation_id": created_reservations[res_index]["id"],
            "seat_id": GENERATED_SEAT_IDS[seat_key],
            "user_id": GENERATED_USER_IDS[user_key],
            "theme": template["theme"],
            "message": template["message"]
        }
        
        await create_ticket(ticket_data, user_cookies[user_key])
    
    print("Mockup data creation completed.")
    print("Generated IDs:")
    print("Users:", GENERATED_USER_IDS)
    print("Seats:", GENERATED_SEAT_IDS)
    print("Reservations:", GENERATED_RESERVATION_IDS)
    print("Tickets:", GENERATED_TICKET_IDS)

if __name__ == "__main__":
    asyncio.run(main())