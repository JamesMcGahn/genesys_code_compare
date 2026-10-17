from unittest.mock import Mock

import pytest

from genesys_code_compare.enums import HTTPMETHOD
from genesys_code_compare.errors.network import (
    NotAuthenticatedException,
    NetworkResponseException,
)
from genesys_code_compare.genesys_api import GenesysAPI
from genesys_code_compare.models.config import Region
from genesys_code_compare.models.genesys import ClientCredentials
from genesys_code_compare.models.network import NetworkResponse
from genesys_code_compare.network import NetworkClient, NetworkThrottle

example_payload = """{'access_token': '3XPaaaAM5Dse2UK32RUE01YzdddwcDDZMr_HQ_36ipS_-aquDJLcSPQi3bIj1CIgr7lcY8tU29X6J5p-uzP6mCJfPkmVGng', 'token_type': 'bearer', 'expires_in': 86399}"""


@pytest.fixture
def network_client():
    return Mock(spec=NetworkClient)


@pytest.fixture
def throttle():
    return Mock(spec=NetworkThrottle)


@pytest.fixture
def api(network_client, throttle):
    return GenesysAPI(network_client, throttle)


@pytest.fixture
def credentials():
    return ClientCredentials(
        client_id="client",
        client_secret="secret",
    )


@pytest.fixture
def region():
    return Region(
        name="test",
        login_url="https://login.example.invalid/oauth/token",
        api_url="https://api.example.invalid",
    )


def test_authenticate_returns_token(
    api, network_client, credentials, region, monkeypatch
):
    network_client.execute.return_value = NetworkResponse(
        ok=True,
        status=200,
        data={
            "access_token": "test-token",
            "expires_in": 3600,
        },
    )

    monkeypatch.setattr(
        "genesys_code_compare.genesys_api.time.monotonic",
        lambda: 1000.0,
    )

    token = api.authenticate(credentials, region)

    assert token.access_token == "test-token"
    assert token.expires_at == 4600.0
    assert token.token_type == "bearer"


def test_authenticate_sends_expected_request(
    api, network_client, throttle, credentials, region
):

    network_client.execute.return_value = NetworkResponse(
        ok=True,
        status=200,
        data={"access_token": "test-token", "expires_in": 3600},
    )

    api.authenticate(credentials, region)
    throttle.wait.assert_called_once_with()
    network_client.execute.assert_called_once()

    request = network_client.execute.call_args.args[0]
    assert request.method == HTTPMETHOD.POST
    assert request.url == region.login_url
    assert request.data == {"grant_type": "client_credentials"}
    assert request.headers == {
        "Authorization": "Basic Y2xpZW50OnNlY3JldA==",
        "Content-Type": "application/x-www-form-urlencoded",
    }


def test_authenticate_rejects_invalid_credentials(
    api, network_client, credentials, region
):
    network_client.execute.return_value = NetworkResponse(
        ok=False,
        status=400,
        data={
            "error": "invalid_client",
            "description": "authentication failed",
            "error_description": "authentication failed",
        },
    )

    with pytest.raises(NotAuthenticatedException) as exc_info:
        api.authenticate(credentials, region)

        assert exc_info.message == "invalid_client: authentication failed"
        assert exc_info.status == 400
        assert exc_info.data == {
            "error": "invalid_client",
            "description": "authentication failed",
            "error_description": "authentication failed",
        }


def test_bad_request_no_payload(api, network_client, credentials, region):
    network_client.execute.return_value = NetworkResponse(
        ok=False,
        status=400,
        data=None,
    )

    with pytest.raises(NetworkResponseException) as exc_info:

        api.authenticate(credentials, region)
        assert (
            exc_info.message
            == "NetworkResponseException: received a failed response from server."
        )
        assert exc_info.status == 400
        assert exc_info.data is None
