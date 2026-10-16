from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class NetworkResponse:
    ok: bool
    status: int
    data: Any
    message: str | None = None
    headers: None | dict = None
