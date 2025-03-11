class SeatIsNotAvailableError(Exception):
    def __init__(self, seat_id='seat id', start='start datetime', end="end datetime", name="name"):
        self.name = name
        self.seat_id = seat_id
        self.start = start
        self.end = end
        message = f"Место с {name} id {seat_id} недоступно в интервале {start} - {end}"
        super().__init__(message)

    def __str__(self):
        return self.args[0]

class UserAlreadyHasActiveReservationError(Exception):
    def __init__(self, user_id='user id'):
        self.user_id = user_id
        message = f"Пользователь с id {user_id} уже имеет активное бронирование"
        super().__init__(message)

    def __str__(self):
        return self.args[0]
