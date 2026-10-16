class RetryableNetworkException(Exception):
    """Rule has duplicate name."""

    def __init__(self, message=None):
        if message is None:
            message = (
                "RetryAbleNetworkException: server returned a failure. Able to retry."
            )
        super().__init__(message)
