from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .activity_code import ActivityCode

from dataclasses import dataclass


@dataclass(frozen=True)
class BusinessUnit:
    bu_id: str
    name: str
    activity_codes: tuple[ActivityCode] = ()
