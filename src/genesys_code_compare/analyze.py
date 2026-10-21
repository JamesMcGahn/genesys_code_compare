from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .cli import CLI

from .models.genesys import BusinessUnit, ActivityCode


from .models.analyze import CodePresence, MatchResult


class ActivityCodeAnalyze:

    def __init__(self, cli: CLI):
        self.cli = cli

    def analyze(self, business_units: list[BusinessUnit]):
        self.cli.print_info("Starting to Analyze Business Units Activity Codes.")
        data_set = {
            bu.name: {code.name: code for code in bu.activity_codes}
            for bu in business_units
        }

        all_codes = set().union(*(codes.keys() for codes in data_set.values()))

        exact_name_matches = []
        exact_field_matches = []
        field_differences = []
        partial_matches = []
        unique = []

        for code in sorted(all_codes):

            code_present_in: dict[str, ActivityCode] = {
                bu_name: bu_codes[code]
                for bu_name, bu_codes in data_set.items()
                if code in bu_codes
            }

            values: list[ActivityCode] = list(code_present_in.values())
            first = self._field_comparison(values[0])
            # Code in ALL BUs

            presence = CodePresence(
                name=code,
                present_in=code_present_in,
                missing_from=sorted(data_set.keys() - code_present_in.keys()),
            )

            if len(values) == len(data_set):

                exact_name_matches.append(presence)

                if all(self._field_comparison(v) == first for v in values[1:]):
                    exact_field_matches.append(presence)
                else:
                    field_differences.append(presence)
            elif len(code_present_in) > 1:
                partial_matches.append(presence)
            else:
                unique.append(presence)

        self.cli.print_status("Completed Analyzing Business Unit's Activity Codes.")
        self.cli.print_status(f"Exact Name Matches: {len(exact_name_matches)}")
        self.cli.print_status(f"Exact Partial Matches: {len(partial_matches)}")
        self.cli.print_status(f"Exact Unique Codes: {len(unique)}")
        return MatchResult(
            exact_name_matches=exact_name_matches,
            exact_field_matches=exact_field_matches,
            field_differences=field_differences,
            partial_matches=partial_matches,
            unique=unique,
        )

    def _field_comparison(self, activity_code: ActivityCode):
        return (
            activity_code.name,
            activity_code.category,
            activity_code.default_code,
        )
