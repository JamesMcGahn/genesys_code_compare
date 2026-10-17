from typing import Any


class NetworkResponseException(Exception):

    def __init__(self, message=None, status: int | None = None, data: Any = None):
        self.status = status
        self.data = data
        if message is None:
            message = (
                "NetworkResponseException: received a failed response from server."
            )
        super().__init__(message)
