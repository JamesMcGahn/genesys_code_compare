from unittest.mock import Mock
from io import BytesIO

import pytest
import requests
from datetime import datetime, timezone
from genesys_code_compare.enums import HTTPMETHOD
from genesys_code_compare.genesys import GenesysAPI
from genesys_code_compare.models.genesys import (
    ClientCredentials,
)
from genesys_code_compare.models.network import (
    AccessToken,
    NetworkRequest,
)
from genesys_code_compare.network import NetworkClient, NetworkThrottle
from genesys_code_compare.cli import CLI

from genesys_code_compare.network.base_api import BaseApi


@pytest.fixture
def cli():
    return Mock(spec=CLI)


@pytest.fixture
def throttle():
    return Mock(spec=NetworkThrottle)


@pytest.fixture
def api(network_client, throttle, cli):
    return GenesysAPI(network_client, throttle, cli)


@pytest.fixture
def credentials():
    return ClientCredentials(
        client_id="client",
        client_secret="secret",
    )


@pytest.fixture
def access_token():
    return AccessToken("123456789", 3600)


@pytest.fixture
def session():
    return Mock(spec=requests.Session)


@pytest.fixture
def network_client(session):
    return NetworkClient(session)


@pytest.fixture
def base_api(network_client, throttle):
    return BaseApi(network_client, throttle)


def test_expected_call_args(network_client, session):
    request = NetworkRequest(
        HTTPMETHOD.GET,
        "text.example",
        {"hamburger": "chicken"},
        {"pizza": "turkey"},
        {"blah": "boo"},
        {"pic": "upload"},
        BytesIO(b"hello world"),
        45,
        1,
    )

    response = Mock()
    response.headers = {"Content-Type": "application/json"}
    response.status_code = 200
    response.ok = True
    response.json.return_value = {"result": "success"}

    session.request.return_value = response

    nc_response = network_client.execute(request)
    session.request.assert_called_once_with(
        method=request.method,
        url=request.url,
        params=request.params,
        headers=request.headers,
        json=request.json,
        data=request.data,
        files=request.files,
        timeout=request.timeout,
    )

    response.json.assert_called_once()

    assert nc_response.ok == True
    assert nc_response.status == 200
    assert nc_response.data == response.json.return_value
    assert nc_response.message == "success"
    assert nc_response.headers == response.headers


def test_response_exception(network_client, session):
    request = NetworkRequest(
        HTTPMETHOD.GET,
        "text.example",
        {"hamburger": "chicken"},
        {"pizza": "turkey"},
        {"blah": "boo"},
        {"pic": "upload"},
        BytesIO(b"hello world"),
        45,
        1,
    )
    session.request.side_effect = requests.RequestException("Connection failed")

    nc_response = network_client.execute(request)

    assert nc_response.ok == False
    assert nc_response.status == 0
    assert nc_response.data is None
    assert nc_response.message == "Connection failed"


@pytest.mark.parametrize(
    ("time", "result"),
    [
        ("120", 120.0),
        ("2.5", 2.5),
        ("0", 0.0),
        ("-10", 0.0),  # Negative delays clamp to zero
        (" 30 ", 30.0),  # Surrounding whitespace
        ("inf", 60.0),
        ("-inf", 60.0),
        ("nan", 60.0),
        ("", 60.0),
        ("not-a-date", 60.0),
        (None, 60.0),
    ],
)
def test_parse_after_time_nums(network_client, time, result):
    response = network_client.parse_retry_after_time(time)
    assert response == result


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        # Future date: wait two minutes
        ("Thu, 22 Oct 2026 12:02:00 GMT", 120.0),
        # Current time: no wait
        ("Thu, 22 Oct 2026 12:00:00 GMT", 0.0),
        # Past date: clamp to zero
        ("Thu, 22 Oct 2026 11:59:00 GMT", 0.0),
        # Different timezone, equivalent to 12:02 UTC
        ("Thu, 22 Oct 2026 14:02:00 +0200", 120.0),
        # No timezone: your code assumes UTC
        ("Thu, 22 Oct 2026 12:02:00", 120.0),
        # Invalid calendar date: use fallback
        ("Thu, 99 Oct 2026 12:02:00 GMT", 60.0),
    ],
)
def test_parse_retry_after_dates(monkeypatch, value, expected):
    fixed = datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc)

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed

    monkeypatch.setattr(
        "genesys_code_compare.network.network_client.datetime",
        FixedDatetime,
    )

    assert NetworkClient.parse_retry_after_time(value) == expected
