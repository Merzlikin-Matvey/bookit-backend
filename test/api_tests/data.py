import uuid
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8080/api"
ADMIN_KEY = "j3h4m1dm4mpk6"

USER_IDS = {
    "admin": uuid.UUID("11111111-1111-1111-1111-111111111111"),
    "user1": uuid.UUID("22222222-2222-2222-2222-222222222222"),
    "user2": uuid.UUID("33333333-3333-3333-3333-333333333333"),
    "manager": uuid.UUID("44444444-4444-4444-4444-444444444444")
}

SEAT_IDS = {
    "seat1": uuid.UUID("55555555-5555-5555-5555-555555555551"),
    "seat2": uuid.UUID("55555555-5555-5555-5555-555555555552"),
    "seat3": uuid.UUID("55555555-5555-5555-5555-555555555553"),
    "seat4": uuid.UUID("55555555-5555-5555-5555-555555555554"),
    "meeting_room": uuid.UUID("55555555-5555-5555-5555-555555555555"),
    "quiet_zone": uuid.UUID("55555555-5555-5555-5555-555555555556")
}

USERS_DATA = [
    {
        "id": USER_IDS["admin"],
        "email": "admin@example.com",
        "first_name": "Admin",
        "role": "admin",
        "password": "adminpass1234", 
        "admin_key": ADMIN_KEY,
    },
    {
        "id": USER_IDS["user1"],
        "email": "user1@example.com",
        "first_name": "Test User",
        "role": "user",
        "password": "userpass1234"
    },
    {
        "id": USER_IDS["user2"],
        "email": "user2@example.com",
        "first_name": "Another User",
        "role": "user",
        "password": "password1234"
    },
    {
        "id": USER_IDS["manager"],
        "email": "manager@example.com",
        "first_name": "Office Manager",
        "role": "user",
        "password": "manager1234"
    }
]

SEATS_DATA = [
    {
        "id": SEAT_IDS["seat1"],
        "x": 10.0,
        "y": 15.0,
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
        "id": SEAT_IDS["seat2"],
        "x": 10.0,
        "y": 20.0,
        "width": 1.0,
        "has_computer": True,
        "has_water": False,
        "has_kitchen": False,
        "has_smart_desk": False,
        "is_quite": True,
        "is_talk_room": False,
        "is_available": True
    },
    {
        "id": SEAT_IDS["seat3"],
        "x": 20.0,
        "y": 15.0,
        "width": 1.0,
        "has_computer": False,
        "has_water": True,
        "has_kitchen": False,
        "has_smart_desk": False,
        "is_quite": False,
        "is_talk_room": False,
        "is_available": True
    },
    {
        "id": SEAT_IDS["seat4"],
        "x": 20.0,
        "y": 20.0,
        "width": 1.0,
        "has_computer": False,
        "has_water": False,
        "has_kitchen": False,
        "has_smart_desk": False,
        "is_quite": False,
        "is_talk_room": False,
        "is_available": True
    },
    {
        "id": SEAT_IDS["meeting_room"],
        "x": 30.0,
        "y": 30.0,
        "width": 4.0,
        "has_computer": True,
        "has_water": True,
        "has_kitchen": False,
        "has_smart_desk": False,
        "is_quite": False,
        "is_talk_room": True,
        "is_available": True
    },
    {
        "id": SEAT_IDS["quiet_zone"],
        "x": 40.0,
        "y": 10.0,
        "width": 1.0,
        "has_computer": False,
        "has_water": True,
        "has_kitchen": False,
        "has_smart_desk": False,
        "is_quite": True,
        "is_talk_room": False,
        "is_available": True
    }
]

today = datetime.now()
tomorrow = today + timedelta(days=1)
next_week = today + timedelta(days=7)

RESERVATION_IDS = {
    "res1": uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
    "res2": uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
    "res3": uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
    "res4": uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
}

RESERVATIONS_DATA = [
    {
        "id": RESERVATION_IDS["res1"],
        "user_id": USER_IDS["user1"],
        "seat_id": SEAT_IDS["seat1"],
        "start_time": today.replace(hour=9, minute=0, second=0, microsecond=0),
        "end_time": today.replace(hour=18, minute=0, second=0, microsecond=0),
        "status": "active"
    },
    {
        "id": RESERVATION_IDS["res2"],
        "user_id": USER_IDS["user2"],
        "seat_id": SEAT_IDS["seat2"],
        "start_time": tomorrow.replace(hour=10, minute=0, second=0, microsecond=0),
        "end_time": tomorrow.replace(hour=16, minute=0, second=0, microsecond=0),
        "status": "pending"
    },
    {
        "id": RESERVATION_IDS["res3"],
        "user_id": USER_IDS["manager"],
        "seat_id": SEAT_IDS["meeting_room"],
        "start_time": tomorrow.replace(hour=14, minute=0, second=0, microsecond=0),
        "end_time": tomorrow.replace(hour=16, minute=0, second=0, microsecond=0),
        "status": "active"
    },
    {
        "id": RESERVATION_IDS["res4"],
        "user_id": USER_IDS["user1"],
        "seat_id": SEAT_IDS["quiet_zone"],
        "start_time": next_week.replace(hour=9, minute=0, second=0, microsecond=0),
        "end_time": next_week.replace(hour=18, minute=0, second=0, microsecond=0),
        "status": "active"
    }
]

TICKET_IDS = {
    "ticket1": uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"),
    "ticket2": uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
}

TICKETS_DATA = [
    {
        "id": TICKET_IDS["ticket1"],
        "user_id": USER_IDS["user1"],
        "reservation_id": RESERVATION_IDS["res1"],
        "seat_id": SEAT_IDS["seat1"],
        "theme": "Проблема с компьютером",
        "message": "Не работает монитор на рабочем месте",
        "status": "open",
        "made_on": today - timedelta(hours=3)
    },
    {
        "id": TICKET_IDS["ticket2"],
        "user_id": USER_IDS["user2"],
        "reservation_id": RESERVATION_IDS["res2"],
        "seat_id": SEAT_IDS["seat2"],
        "theme": "Нужен дополнительный доступ",
        "message": "Требуется доступ к переговорной комнате",
        "status": "closed",
        "made_on": today - timedelta(days=1)
    }
]