import asyncio
import random
from server.backend.metrics import (
    user_registrations_total,
    user_logins_total,
    active_users,
    session_duration_seconds,
    api_errors_total,
    bookings_total,
    average_booking_time_seconds
)

async def simulate_day_and_metrics():
    """
    Background task: updates statistics (increments metrics) every second.
    """
    while True:
        # Simulate user registrations and logins
        user_registrations_total.inc(random.randint(1, 5))
        user_logins_total.inc(random.randint(5, 20))

        # Simulate active users and session durations
        active_users.set(random.randint(50, 200))
        session_duration_seconds.set(random.uniform(300, 3600))

        # Simulate bookings and average booking time
        bookings_total.inc(random.randint(1, 10))
        average_booking_time_seconds.set(random.uniform(600, 3600))

        # Simulate API errors occasionally (20% chance per second) с указанием ярлыка
        if random.random() < 0.2:
            api_errors_total.labels(endpoint="default").inc(random.randint(1, 3))

        await asyncio.sleep(1)
