from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .network.network_client import NetworkClient
    from .network.network_throttle import NetworkThrottle
    from .cli import CLI
import base64
from .network.base_api import BaseApi
from .enums import HTTPMETHOD
from .models.network import NetworkRequest, NetworkResponse, AccessToken
from .models.genesys import ClientCredentials, BusinessUnit
from .models.config import Region
import time
from .errors.network import NotAuthenticatedException, NetworkResponseException


class GenesysAPI(BaseApi):

    def __init__(
        self, network_client: NetworkClient, network_throttle: NetworkThrottle, cli: CLI
    ):
        super().__init__(network_client, network_throttle)
        self.cli = cli

    def authenticate(
        self, client_credentials: ClientCredentials, region: Region
    ) -> AccessToken:
        credentials = (
            f"{client_credentials.client_id}:{client_credentials.client_secret}"
        )
        authorization = base64.b64encode(bytes(credentials, "ISO-8859-1")).decode(
            "ascii"
        )

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
        self.cli.print_info("Sending request for access token.")
        self._network_throttle.wait()
        response = self._execute(request)
        self._handle_response(response)

        if response.data is None or "access_token" not in response.data:
            self.cli.print_error("Received response. Access token not in payload.")
            raise NotAuthenticatedException(
                "access token not in payload.", response.status, response.data
            )
        self.cli.print_status("Successfully received response for access token.")
        return AccessToken(
            access_token=response.data["access_token"],
            expires_at=time.monotonic() + int(response.data["expires_in"]),
        )

    def get_business_units(
        self, access_token: AccessToken, region: Region
    ) -> list[BusinessUnit]:

        url = f"{region.api_url}/api/v2/workforcemanagement/businessunits"
        request_headers = {
            "Authorization": f"Bearer {access_token.access_token}",
            "Content-Type": "application/json",
        }

        request = NetworkRequest(
            method=HTTPMETHOD.GET,
            headers=request_headers,
            url=url,
        )

        self._network_throttle.wait()
        self.cli.print_info("Sending request for business units.")
        response = self._execute(request)
        self._handle_response(response)

        return self._parse_business_units(response)

    def _parse_business_units(self, response: NetworkResponse) -> list[BusinessUnit]:
        payload = response.data
        if payload is None or "entities" not in payload:
            error_message = "No Business Units were included in the response."
            self.cli.print_error(error_message)
            raise NetworkResponseException(
                "No Business Units were included in the response.",
                response.status,
                payload,
            )

        entities: list[dict[str, Any]] = payload["entities"]

        bu_list = []
        for bu in entities:
            n_bu_id = bu.get("id")
            n_bu_name = bu.get("name")

            if not n_bu_id or not n_bu_name:
                bu_msg_part = (
                    n_bu_id if not n_bu_name else n_bu_name if not n_bu_id else ""
                )
                missing = "a name" if not n_bu_name else "an id"
                message = f"Skipping BU - {bu_msg_part} as it doesnt have {missing}"
                self.cli.print_warn(message)
                continue

            bu_list.append(BusinessUnit(bu_id=n_bu_id, name=n_bu_name))

        if not bu_list:
            error_message = "No Business Units were including in the response."
            self.cli.print_error(error_message)
            raise NetworkResponseException(message, response.status, payload)
        self.cli.print_status(f"Successfully received {len(bu_list)} business units.")
        return bu_list
