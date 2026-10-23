from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models.network import AccessToken
    from .models.genesys import BusinessUnit, Region
from .app_config import AppConfig
from .cli import CLI
from .models.genesys import ClientCredentials

from requests import Session
from .network import NetworkClient, NetworkThrottle
from .genesys import GenesysAPI
from .prompts import Prompts
from .enums import RUN_MENU
import sys
from .workflows import Workflow, CompareActivityCodes, AuthFlow
from .analyze import ActivityCodeAnalyze
from .file import AnalyzeSheetService
from .errors.network import NetworkResponseException, RetryableNetworkException


class App:

    def __init__(
        self,
    ):
        self.cli = CLI()
        self._app_config = AppConfig(self.cli)
        self._config = None
        self._http_session = Session()
        self._network_throttle = NetworkThrottle()
        self._network_client = NetworkClient(self._http_session)
        self._gen_api = GenesysAPI(
            self._network_client, self._network_throttle, self.cli
        )
        self.prompts = Prompts(self.cli)
        self.activity_code_analyzer = ActivityCodeAnalyze(self.cli)
        self.activity_code_reports = AnalyzeSheetService(self.cli)

        self._gen_token: AccessToken | None = None
        self._region: Region | None = None
        self._client_creds: ClientCredentials | None = None

    def run(self):

        self.start_up()
        auth_flow = AuthFlow(
            cli=self.cli,
            genesys_api=self._gen_api,
            prompts=self.prompts,
            config=self._app_config,
        )
        session = auth_flow.run()

        workflows: dict[RUN_MENU, Workflow] = {
            RUN_MENU.COMPARE_ACTIVITY_CODES: CompareActivityCodes(
                cli=self.cli,
                gen_api=self._gen_api,
                gen_session=session,
                prompts=self.prompts,
                analyzer=self.activity_code_analyzer,
                reports=self.activity_code_reports,
            ),
        }

        while True:
            choice = self.prompts.welcome_menu()
            if choice == RUN_MENU.QUIT:
                sys.exit(0)
            elif choice == RUN_MENU.COMPARE_ACTIVITY_CODES:
                try:
                    workflows[choice].run()
                except RetryableNetworkException:
                    self.cli.print_error(
                        "Genesys is temporarily unavailable or rate limiting requests. "
                        "Wait before trying again."
                    )
                except NetworkResponseException as error:
                    if error.status == 0:
                        self.cli.print_error(
                            "Cannot reach Genesys. Check your connection."
                        )
                    elif error.status == 403:
                        self.cli.print_error(
                            "Access denied. Check the client's permissions."
                        )
                    else:
                        self.cli.print_error(f"Genesys request failed: {error}")
                except PermissionError:
                    self.cli.print_error(
                        "Cannot write the report. Close it in Excel "
                        "and check the output folder's permissions."
                    )
                except OSError as error:
                    self.cli.print_error(f"Cannot save the report: {error}")

    def start_up(self):
        self._app_config.load_config()
        self.prompts.welcome_message()
