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
        ]

        row_data = [
            [
                record.name,
                bu_name,
                code.category,
                code.default_code,
                code.default_name_changed,
                code.ac_id,
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
            ]
            for record in records
        ]

        return SheetData(name="Summary", headers=["Code", *bu_names], rows=data_rows)
