from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models.config import Region
    from .models.network import AccessToken
    from .models.genesys import BusinessUnit
from .app_config import AppConfig
from .cli import CLI
from .models.genesys import ClientCredentials

from requests import Session
from .network import NetworkClient, NetworkThrottle
from .genesys_api import GenesysAPI
from .prompts import Prompts


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
        self._gen_api = GenesysAPI(
            self._network_client, self._network_throttle, self.cli
        )
        self.prompts = Prompts(self.cli)

        self._gen_token: AccessToken | None = None
        self._region: Region | None = None
        self._client_creds: ClientCredentials | None = None

    def run(self):
        self._config = self.app_config.load_config()
        print(self._config)
        self.prompts.welcome_message()
        self.prompts.welcome_menu()
        self._client_creds = self.prompts.enter_client_credentials()
        self._region = self.prompts.prompt_user_for_region(self._config)
        self._gen_token = self._gen_api.authenticate(self._client_creds, self._region)
        full_bus = self._gen_api.get_business_units(self._gen_token, self._region)
        self.prompts.prompt_user_for_bus(full_bus)

    def check_token_before(self):
        if self._client_creds is None or self._region is None:
            raise RuntimeError

        if self._gen_token is None or self._gen_token.is_expired():
            self._gen_token = self._gen_api.authenticate(
                self._client_creds, self._region
            )
