from dataclasses import dataclass
from typing import Any, Mapping
from ...enums.http_method import HTTPMETHOD
import time


@dataclass(frozen=True)
class AccessToken:
    access_token: str
    expires_at: int
    token_type: str = "bearer"

    def is_expired(self, buffer_seconds: float = 60) -> bool:
        return time.monotonic() >= self.expires_at - buffer_seconds
