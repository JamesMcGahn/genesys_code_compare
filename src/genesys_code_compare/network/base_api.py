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

        match response.status:
            case 0:
                raise NetworkResponseException
            case 401:
                raise NotAuthenticatedException
            case 429:
                retry_after = response.headers.get("Retry-After")

                if retry_after:
                    delay = self._client.parse_retry_after_time(retry_after)
                    self._network_throttle.delay(delay)

                self._network_throttle.increase_wait_interval()
                raise RetryableNetworkException
            case 408 | 500 | 502 | 503 | 504:
                self._network_throttle.delay(5.0)
                raise RetryableNetworkException
            case status if status >= 400:
                raise NetworkResponseException
            case _:
                return
