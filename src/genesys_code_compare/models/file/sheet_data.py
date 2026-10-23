from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, datetime

CellValue = str | int | float | bool | date | datetime | None


@dataclass
class SheetData:
    name: str
    headers: Sequence[str]
    rows: Iterable[Sequence[CellValue]]
