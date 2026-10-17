from typing import Any


class NotAuthenticatedException(Exception):
    """Rule has duplicate name."""

    def __init__(self, message=None, status: int | None = None, data: Any = None):
        self.status = status
        self.data = data
        if message is None:
            message = (
                "NotAuthenticatedException: Server returned not authenticated response."
            )
        super().__init__(message)
