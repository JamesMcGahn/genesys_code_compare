from unittest.mock import Mock

import pytest

from genesys_code_compare.enums import HTTPMETHOD
from genesys_code_compare.errors.network import (
    NotAuthenticatedException,
    NetworkResponseException,
    RetryableNetworkException,
)
from genesys_code_compare.genesys import GenesysAPI
from genesys_code_compare.models.genesys import (
    ClientCredentials,
)
from genesys_code_compare.models.network import (
    NetworkResponse,
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
def network_client():
    return Mock(spec=NetworkClient)


@pytest.fixture
def base_api(network_client, throttle):
    return BaseApi(network_client, throttle)


def test_execute(base_api, network_client):
    request = NetworkRequest(HTTPMETHOD.GET, "example.com")

    expected = NetworkResponse(
        True, 200, {"success": True}, "success", {"test": "test"}
    )
    network_client.execute.return_value = expected
    response = base_api._execute(request)
    assert response is expected
    network_client.execute.assert_called_once()


@pytest.mark.parametrize("status", [400, 402])
def test_handle_response_response_error(base_api, status):
    response = NetworkResponse(
        False, status, {"error": "error"}, "error message", {"test": "test"}
    )

    with pytest.raises(NetworkResponseException) as exc_info:
        base_api._handle_response(response)

    e = exc_info.value
    assert e.status == status
    assert str(e) == "error"
    assert e.data == response.data


@pytest.mark.parametrize("status", [400, 401])
def test_handle_response_auth_error(base_api, status):
    response = NetworkResponse(
        False, status, {"error": "invalid_client"}, "error message", {"test": "test"}
    )

    with pytest.raises(NotAuthenticatedException) as exc_info:
        base_api._handle_response(response)

    e = exc_info.value
    assert e.status == status
    assert str(e) == "invalid_client"
    assert e.data == response.data


@pytest.mark.parametrize("status", [408, 500, 502, 503, 504, 429])
def test_handle_response_retryable_error(base_api, status):
    response = NetworkResponse(
        False, status, {"error": "network"}, "error message", {"test": "test"}
    )

    with pytest.raises(RetryableNetworkException) as exc_info:
        base_api._handle_response(response)

    e = exc_info.value
    assert e.status == status
    assert str(e) == "network"
    assert e.data == response.data


@pytest.mark.parametrize("status", [429])
def test_handle_response_retryable_with_increase(
    base_api, status, throttle, network_client
):
    response = NetworkResponse(
        False, status, {"error": "network"}, "error message", {"Retry-After": 60}
    )
    network_client.parse_retry_after_time.return_value = 60.0
    with pytest.raises(RetryableNetworkException) as exc_info:
        base_api._handle_response(response)

    network_client.parse_retry_after_time.assert_called_once_with(60)

    throttle.delay.assert_called_once_with(60.0)
    throttle.increase_wait_interval.assert_called_once()

    e = exc_info.value
    assert e.status == status
    assert str(e) == "network"
    assert e.data == response.data


def test_handle_response_expected(base_api, throttle, network_client):
    response = NetworkResponse(
        True, 200, {"error": "network"}, "error message", {"Retry-After": 60}
    )
    call_res = base_api._handle_response(response)
    assert call_res is None


@pytest.mark.parametrize(
    ("payload", "msg"),
    [
        ({"error": "err_msg"}, "err_msg"),
        ({"error": "err_msg", "description": "err_msg_d"}, "err_msg: err_msg_d"),
        ({"message": "err_msg_m"}, "err_msg_m"),
    ],
)
def test_handle_error_messages(base_api, payload, msg):
    response = NetworkResponse(False, 0, payload, "error message", {"Retry-After": 60})

    with pytest.raises(NetworkResponseException) as exc_info:
        base_api._handle_response(response)

    e = exc_info.value
    assert e.status == 0
    assert str(e) == msg
    assert e.data == response.data
