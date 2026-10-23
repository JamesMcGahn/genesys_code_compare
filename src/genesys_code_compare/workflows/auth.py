from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..cli import CLI
    from ..genesys import GenesysAPI
    from ..prompts import Prompts
    from ..app_config import AppConfig


from ..genesys import GenesysSession
from ..errors.network import NotAuthenticatedException


class AuthFlow:

    def __init__(
        self,
        cli: CLI,
        genesys_api: GenesysAPI,
        prompts: Prompts,
        config: AppConfig,
    ):
        self._genesys_api = genesys_api
        self._prompts = prompts
        self._config = config
        self._cli = cli
        self._session: None | GenesysSession = None

    def run(self) -> GenesysSession:

        while True:
            try:
                client_creds = self._prompts.enter_client_credentials()
                region = self._prompts.prompt_user_for_region(self._config.region_list)

                self._session = GenesysSession(self._genesys_api, client_creds, region)
                self._session.get_valid_token()
                return self._session
            except NotAuthenticatedException:
                self._cli.print_error(
                    "Authentication failed. Check your client ID, client secret, and region. Try again."
                )
