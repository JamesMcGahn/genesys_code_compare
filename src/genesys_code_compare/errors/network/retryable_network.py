from typing import Any


class RetryableNetworkException(Exception):

    def __init__(self, message=None, status: int | None = None, data: Any = None):
        self.status = status
        self.data = data
        if message is None:
            message = (
                "RetryAbleNetworkException: server returned a failure. Able to retry."
            )
        super().__init__(message)
