import uuid
from datetime import datetime, timedelta
import httpx
import asyncio
import json

BASE_URL = "https://prod-team-17-61ojpp1i.final.prodcontest.ru/api"
# BASE_URL = "http://localhost:8080/api"

ADMIN_KEY = "j3h4m1dm4mpk6"
VERIFY_SSL = False

USERS_DATA = [
    {
        "email": f"demo_email_{i}@example.com",
        "first_name": f"User {i}",
        "password": "password123",
        "role": "user"
    }
    for i in range(10)
]

ADMINS_DATA = [
    {
        "email": f"demo_admin_{i}@example.com",
        "first_name": f"Admin {i}",
        "password": "password123",
        "role": "admin",
        "admin_key": ADMIN_KEY
    } for i in range(10)
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
                    "admin_key": user_data.get("admin_key")
                }
            )
            if response.status_code in [200, 201]:
                user_response = response.json()
                if "user" in user_response:
                    print(f"email: {user_data['email']}    password: {user_data['password']}")
                    return user_response["user"], response.cookies
                else:
                    print(f"User data not found in response: {user_response}")
                    return None, None
            else:
                print(f"Failed to register user {user_data['email']}: {response.status_code}, {response.text}")
                return None, None
    except Exception as e:
        print(f"Error registering user {user_data['email']}: {str(e)}")
        return None, None

async def main():
    print("\n=== Registering Regular Users ===")
    for user_data in USERS_DATA:
        await register_user(user_data)
    
    print("\n=== Registering Admin Users ===")
    for admin_data in ADMINS_DATA:
        await register_user(admin_data)
    
    print("\nRegistration complete.")

if __name__ == "__main__":
    asyncio.run(main())
