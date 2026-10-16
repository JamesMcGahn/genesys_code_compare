from dataclasses import dataclass
from typing import Any, Mapping
from ...enums.http_method import HTTPMETHOD


@dataclass(frozen=True)
class NetworkRequest:
    method: HTTPMETHOD
    url: str
    params: Mapping[str, Any] | None = None
    headers: Mapping[str, str] | None = None
    json: Any = None
    data: Any = None
    files: Any = None
    timeout: float = 30.0
    retries: int = 0
