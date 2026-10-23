from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..cli import CLI
    from ..genesys import GenesysAPI, GenesysSession
    from ..prompts import Prompts
    from ..analyze import ActivityCodeAnalyze
    from ..file import AnalyzeSheetService
    from ..models.genesys import BusinessUnit, Region
    from ..models.network import AccessToken


class CompareActivityCodes:

    def __init__(
        self,
        cli: CLI,
        gen_api: GenesysAPI,
        gen_session: GenesysSession,
        prompts: Prompts,
        analyzer: ActivityCodeAnalyze,
        reports: AnalyzeSheetService,
    ):
        self._gen_api = gen_api
        self._gen_session = gen_session
        self._prompts = prompts
        self._analyzer = analyzer
        self._reports = reports

    def run(self) -> None:
        token = self._gen_session.get_valid_token()

        region = self._gen_session.region
        business_units = self._gen_api.get_business_units(token, region)
        selected = self._prompts.prompt_user_for_bus(business_units)
        populated = self._get_all_bus_activity_codes(token, region, selected)
        result = self._analyzer.analyze(populated)
        output = self._reports.get_output_path()
        self._reports.write_analyze(populated, result, output)

    def _get_all_bus_activity_codes(
        self, token: AccessToken, region: Region, business_units: list[BusinessUnit]
    ) -> list[BusinessUnit]:
        updated_bus = []
        for bu in business_units:
            updated_bus.append(
                self._gen_api.get_business_unit_activity_codes(token, region, bu)
            )
        return updated_bus
