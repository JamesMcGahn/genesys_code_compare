from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .code_presence import CodePresence
from dataclasses import dataclass, field


@dataclass
class MatchResult:
    exact_name_matches: list[CodePresence] = field(default_factory=list)
    exact_field_matches: list[CodePresence] = field(default_factory=list)
    field_differences: list[CodePresence] = field(default_factory=list)
    partial_matches: list[CodePresence] = field(default_factory=list)
    unique: list[CodePresence] = field(default_factory=list)
