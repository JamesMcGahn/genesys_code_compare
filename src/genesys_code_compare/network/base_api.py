from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.network.network_request import NetworkRequest
    from ..models.network.network_response import NetworkResponse

from .network_client import NetworkClient
from .network_throttle import NetworkThrottle
from ..errors.network import (
    NetworkResponseException,
    RetryableNetworkException,
    NotAuthenticatedException,
)


class BaseApi:
    """Base case for Api"""

    def __init__(
        self, network_client: NetworkClient, network_throttle: NetworkThrottle
    ):
        super().__init__()
        self._client = network_client
        self._network_throttle = network_throttle

    def _execute(self, request: NetworkRequest) -> NetworkResponse:
        return self._client.execute(request)

    def _handle_response(self, response: NetworkResponse):
        error_message = ""
        if response.data is not None and "error" in response.data:
            payload_error = response.data["error"]
            error_message = f"{payload_error}"
            if "description" in response.data:
                description = response.data["description"]
                error_message = f"{payload_error}: {description}"

        match response.status:
            case 0:
                raise NetworkResponseException(
                    error_message or None, response.status, response.message
                )
            case 400:
                if "invalid_client" in error_message:
                    raise NotAuthenticatedException(
                        error_message or None, response.status, response.message
                    )
                raise NetworkResponseException(
                    error_message or None, response.status, response.message
                )
            case 401:
                raise NotAuthenticatedException(
                    error_message or None, response.status, response.message
                )
            case 429:
                retry_after = response.headers.get("Retry-After")

                if retry_after:
                    delay = self._client.parse_retry_after_time(retry_after)
                    self._network_throttle.delay(delay)

                self._network_throttle.increase_wait_interval()
                raise RetryableNetworkException(
                    error_message or None, response.status, response.message
                )
            case 408 | 500 | 502 | 503 | 504:
                self._network_throttle.delay(5.0)
                raise RetryableNetworkException(
                    error_message or None, response.status, response.message
                )
            case status if status >= 400:
                raise NetworkResponseException(
                    error_message or None, response.status, response.message
                )
            case _:
                return
