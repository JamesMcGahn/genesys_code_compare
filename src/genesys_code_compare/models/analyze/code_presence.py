from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..genesys import ActivityCode
from dataclasses import dataclass


@dataclass
class CodePresence:
    name: str
    present_in: dict[str, ActivityCode]
    missing_from: list[str]
