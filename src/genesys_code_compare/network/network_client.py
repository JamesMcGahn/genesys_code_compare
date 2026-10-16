from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from requests import Session
    from ..models.network.network_request import NetworkRequest
from requests import Response, RequestException
from ..models.network.network_response import NetworkResponse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from math import isfinite


class NetworkClient:

    def __init__(self, session: Session):
        self._session = session

    def execute(self, request: NetworkRequest):
        session = self._session

        try:
            response = session.request(
                method=request.method,
                url=request.url,
                params=request.params,
                headers=request.headers,
                json=request.json,
                data=request.data,
                files=request.files,
                timeout=request.timeout,
            )

        except RequestException as e:
            return NetworkResponse(ok=False, status=0, data=None, message=f"{e}")

        return NetworkResponse(
            ok=True,
            status=response.status_code,
            data=self._extract_payload(response),
            message="success" if response.ok else "error",
            headers=response.headers,
        )

    @staticmethod
    def _extract_payload(response: Response) -> Any:
        content_type = response.headers.get("Content-Type", "").lower()
        if "json" in content_type:
            try:
                return response.json()
            except ValueError:
                pass
        return response.text

    @staticmethod
    def parse_retry_after_time(value: str) -> float:
        try:
            delay = float(value)
            if not isfinite(delay):
                return 60.0

            return max(0.0, delay)
        except ValueError, TypeError:
            pass

        try:
            retry_at = parsedate_to_datetime(value)
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            return max(0.0, (retry_at - now).total_seconds())
        except TypeError, ValueError, OverflowError:
            return 60.0
