from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models.config import Region
    from .models.network import AccessToken
from .app_config import AppConfig
from .cli import CLI
from .models.genesys import ClientCredentials

from requests import Session
from .network import NetworkClient, NetworkThrottle
from .genesys_api import GenesysAPI


class App:

    def __init__(
        self,
    ):
        self.cli = CLI()
        self.app_config = AppConfig(self.cli)
        self._config = None
        self._session = Session()
        self._network_throttle = NetworkThrottle()
        self._network_client = NetworkClient(self._session)
        self._gen_api = GenesysAPI(self._network_client, self._network_throttle)
        self._gen_token: AccessToken | None = None
        self._region: Region | None = None
        self._client_creds: ClientCredentials | None = None

    def run(self):
        self._config = self.app_config.load_config()
        print(self._config)
        self.cli.welcome_message()
        self.cli.welcome_menu()
        self._client_creds = self.cli.enter_client_credentials()
        self._region = self.prompt_user_for_region()
        self._gen_token = self._gen_api.authenticate(self._client_creds, self._region)

    def check_token_before(self):
        if self._client_creds is None or self._region is None:
            raise RuntimeError

        if self._gen_token is None or self._gen_token.is_expired():
            self._gen_token = self._gen_api.authenticate(
                self._client_creds, self._region
            )

    def prompt_user_for_region(self):
        region_list = [region.name for region in self._config]
        region_name = self.cli.select_region(region_list)

        if region_name is None:
            raise KeyboardInterrupt

        for region in self._config:
            if region.name == region_name:
                return region

        raise RuntimeError(f"Selected region was not found: {region_name}")
