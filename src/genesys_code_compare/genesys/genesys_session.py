from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.genesys import ClientCredentials, Region
    from ..models.network import AccessToken
    from .genesys_api import GenesysAPI


class GenesysSession:

    def __init__(self, api: GenesysAPI, credentials: ClientCredentials, region: Region):
        self._api = api
        self._credentials = credentials
        self._region = region
        self._token: AccessToken | None = None

    @property
    def region(self) -> Region:
        return self._region

    def get_valid_token(self) -> AccessToken:
        if self._credentials is None or self._region is None:
            message = "Credentials or region is None."

            raise RuntimeError(message)

        if self._token is None or self._token.is_expired():
            self._token = self._api.authenticate(self._credentials, self._region)

        return self._token
