from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .network.network_client import NetworkClient
    from .network.network_throttle import NetworkThrottle

import base64
from .network.base_api import BaseApi
from .enums import HTTPMETHOD
from .models.network import NetworkRequest, NetworkResponse, AccessToken
from .models.genesys import ClientCredentials
from .models.config import Region
import time


class GenesysAPI(BaseApi):

    def __init__(
        self, network_client: NetworkClient, network_throttle: NetworkThrottle
    ):
        super().__init__(network_client, network_throttle)

    def authenticate(
        self, client_credentials: ClientCredentials, region: Region
    ) -> AccessToken:
        authorization = base64.b64encode(
            bytes(
                client_credentials.client_id + ":" + client_credentials.client_secret,
                "ISO-8859-1",
            )
        ).decode("ascii")

        request_headers = {
            "Authorization": f"Basic {authorization}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        request = NetworkRequest(
            method=HTTPMETHOD.POST,
            headers=request_headers,
            url=region.login_url,
            data={"grant_type": "client_credentials"},
        )

        self._network_throttle.wait()
        response = self._execute(request)
        self._handle_response(response)

        if "access_token" not in response.data:
            # TODO: change to more meaningful error
            raise Exception

        return AccessToken(
            access_token=response.data["access_token"],
            expires_at=time.monotonic() + int(response.data["expires_in"]),
        )
