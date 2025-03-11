from prometheus_client import Counter, Gauge

user_registrations_total = Counter('user_registrations_total', 'Total number of user registrations')
user_logins_total = Counter('user_logins_total', 'Total number of user logins')

active_users = Gauge('active_users', 'Number of active users')
session_duration_seconds = Gauge('session_duration_seconds', 'Duration of user sessions in seconds')

api_errors_total = Counter('api_errors_total', 'Total number of API errors', ['endpoint'])

bookings_total = Counter('bookings_total', 'Total number of bookings')
average_booking_time_seconds = Gauge('average_booking_time_seconds', 'Average booking time in seconds')