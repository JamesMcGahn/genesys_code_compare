from .sheet_service import SheetService
from ..cli import CLI
from ..models.analyze import MatchResult
from pathlib import Path
from ..models.file import SheetData
from ..models.genesys import BusinessUnit
from ..models.analyze import CodePresence


class AnalyzeSheetService(SheetService):

    def __init__(self, cli: CLI):
        super().__init__(cli)

    def write_analyze(
        self,
        business_units: list[BusinessUnit],
        match_result: MatchResult,
        output_path: Path | str,
    ) -> Path:
        pass

        sheets = [
            self._build_summary(business_units, match_result),
            self._build_detail_sheet("Exact Matches", match_result.exact_field_matches),
            self._build_detail_sheet(
                "Field Differences", match_result.field_differences
            ),
            self._build_detail_sheet("Partial Matches", match_result.partial_matches),
            self._build_detail_sheet("Unique Codes", match_result.unique),
            self._build_inactive_sheet(business_units),
        ]

        return self.write(output_path, sheets)

    def _build_detail_sheet(self, title: str, records: list[CodePresence]) -> SheetData:
        headers = [
            "Code",
            "Business Unit",
            "Category",
            "Default Code",
            "Default Name Changed",
            "ID",
            "Trailing Spaces",
        ]

        row_data = [
            [
                record.name,
                bu_name,
                code.category,
                code.default_code,
                code.default_name_changed,
                code.ac_id,
                self._trailing_spaces(record.name),
            ]
            for record in sorted(
                records,
                key=lambda record: record.name,
            )
            for bu_name, code in sorted(record.present_in.items())
        ]

        return SheetData(
            name=title,
            headers=headers,
            rows=row_data,
        )

    def _build_summary(
        self, business_units: list[BusinessUnit], match_result: MatchResult
    ) -> SheetData:
        bu_names = [bu.name for bu in business_units]

        data_rows = []
        records = [
            *match_result.exact_name_matches,
            *match_result.partial_matches,
            *match_result.unique,
        ]

        data_rows = [
            [
                record.name,
                *["X" if bu_name in record.present_in else "O" for bu_name in bu_names],
                self._trailing_spaces(record.name),
            ]
            for record in records
        ]

        return SheetData(
            name="Summary", headers=["Code", *bu_names, "Trailing Spaces"], rows=data_rows
        )

    @staticmethod
    def _trailing_spaces(name: str) -> int:
        return len(name) - len(name.rstrip(" "))

    def _build_inactive_sheet(self, business_units: list[BusinessUnit]) -> SheetData:
        rows = [
            [
                code.name,
                bu.name,
                code.category,
                code.default_code,
                code.default_name_changed,
                code.ac_id,
                self._trailing_spaces(code.name),
            ]
            for bu in business_units
            for code in bu.activity_codes
            if not code.is_active
        ]

        rows.sort(key=lambda row: (row[0], row[1], row[5]))

        return SheetData(
            name="Inactive Codes",
            headers=[
                "Code",
                "Business Unit",
                "Category",
                "Default Code",
                "Default Name Changed",
                "ID",
                "Trailing Spaces",
            ],
            rows=rows,
        )
