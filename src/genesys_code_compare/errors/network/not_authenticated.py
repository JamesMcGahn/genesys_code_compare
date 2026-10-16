class NotAuthenticatedException(Exception):
    """Rule has duplicate name."""

    def __init__(self, message=None):
        if message is None:
            message = (
                "NotAuthenticatedException: Server returned not authenticated response."
            )
        super().__init__(message)
