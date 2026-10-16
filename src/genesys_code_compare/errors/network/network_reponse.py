class NetworkResponseException(Exception):
    """Rule has duplicate name."""

    def __init__(self, message=None):
        if message is None:
            message = (
                "NetworkResponseException: received a failed response from server."
            )
        super().__init__(message)
