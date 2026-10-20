from unittest.mock import Mock

import pytest

from genesys_code_compare.enums import HTTPMETHOD
from genesys_code_compare.errors.network import (
    NotAuthenticatedException,
    NetworkResponseException,
)
from genesys_code_compare.genesys_api import GenesysAPI
from genesys_code_compare.models.config import Region
from genesys_code_compare.models.genesys import ClientCredentials, BusinessUnit
from genesys_code_compare.models.network import NetworkResponse, AccessToken
from genesys_code_compare.network import NetworkClient, NetworkThrottle
from genesys_code_compare.cli import CLI


@pytest.fixture
def cli():
    return Mock(spec=CLI)


@pytest.fixture
def network_client():
    return Mock(spec=NetworkClient)


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
def region():
    return Region(
        name="test",
        login_url="https://login.example.invalid/oauth/token",
        api_url="https://api.example.invalid",
    )


def test_authenticate_returns_token(
    api, network_client, credentials, region, cli, monkeypatch
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

    cli.print_info.assert_called_once_with("Sending request for access token.")
    cli.print_status.assert_called_once_with(
        "Successfully received response for access token."
    )
    assert token == AccessToken("test-token", 4600.0, "bearer")


def test_authenticate_sends_expected_request(
    api, network_client, throttle, credentials, region, cli
):

    network_client.execute.return_value = NetworkResponse(
        ok=True,
        status=200,
        data={"access_token": "test-token", "expires_in": 3600},
    )

    api.authenticate(credentials, region)
    throttle.wait.assert_called_once_with()
    network_client.execute.assert_called_once()

    cli.print_info.assert_called_once_with("Sending request for access token.")
    cli.print_status.assert_called_once_with(
        "Successfully received response for access token."
    )

    request = network_client.execute.call_args.args[0]
    assert request.method == HTTPMETHOD.POST
    assert request.url == region.login_url
    assert request.data == {"grant_type": "client_credentials"}
    assert request.headers == {
        "Authorization": "Basic Y2xpZW50OnNlY3JldA==",
        "Content-Type": "application/x-www-form-urlencoded",
    }


def test_authenticate_rejects_invalid_credentials(
    api, network_client, credentials, region, cli
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
        cli.print_error.assert_called_once_with(
            "Received response. Access token not in payload."
        )
        assert exc_info.message == "invalid_client: authentication failed"
        assert exc_info.status == 400
        assert exc_info.data == {
            "error": "invalid_client",
            "description": "authentication failed",
            "error_description": "authentication failed",
        }


def test_bad_request_no_payload(api, network_client, credentials, region, cli):
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


def test_unathenticated_call(api, network_client, credentials, region):
    network_client.execute.return_value = NetworkResponse(
        ok=False,
        status=401,
        data={
            "message": "Invalid login credentials.",
            "code": "bad.credentials",
            "status": 401,
            "contextId": "b3892cfd-11ba-40a6-8f16-2ee8272de3ff",
            "details": [],
            "errors": [],
        },
    )

    with pytest.raises(NotAuthenticatedException) as exc_info:
        api.authenticate(credentials, region)

    e = exc_info.value

    assert str(e) == "Invalid login credentials."
    assert e.status == 401
    assert e.data == {
        "message": "Invalid login credentials.",
        "code": "bad.credentials",
        "status": 401,
        "contextId": "b3892cfd-11ba-40a6-8f16-2ee8272de3ff",
        "details": [],
        "errors": [],
    }


def test_bu_sends_expected_request(
    api, network_client, throttle, cli, region, access_token
):
    network_client.execute.return_value = NetworkResponse(
        ok=True,
        status=200,
        data={
            "entities": [
                {
                    "id": "1f271csd-ff47-4ead-8343-323ac1751ed6",
                    "name": "Test BU",
                    "authorized": False,
                    "division": {
                        "id": "0c1a7c06-45ar-441e-a3d5-94add1fa9658",
                        "selfUri": "/api/v2/authorization/divisions/0c1a7c06-45ar-441e-a3d5-94add1fa9658",
                    },
                    "selfUri": "/api/v2/workforcemanagement/businessunits/1f271csd-ff47-4ead-8343-323ac1751ed6",
                }
            ]
        },
    )

    api.get_business_units(access_token, region)
    throttle.wait.assert_called_once_with()
    cli.print_info.assert_called_once_with("Sending request for business units.")
    network_client.execute.assert_called_once()

    cli.print_status.assert_called_once_with("Successfully received 1 business units.")

    request = network_client.execute.call_args.args[0]
    assert request.method == HTTPMETHOD.GET
    assert request.url == f"{region.api_url}/api/v2/workforcemanagement/businessunits"
    assert request.headers == {
        "Authorization": f"Bearer 123456789",
        "Content-Type": "application/json",
    }


def test_expected_bu_response(api, network_client, throttle, cli, region, access_token):
    network_client.execute.return_value = NetworkResponse(
        ok=True,
        status=200,
        data={
            "entities": [
                {
                    "id": "1f271csd-ff47-4ead-8343-323ac1751ed6",
                    "name": "Test BU",
                    "authorized": False,
                    "division": {
                        "id": "0c1a7c06-45ar-441e-a3d5-94add1fa9658",
                        "selfUri": "/api/v2/authorization/divisions/0c1a7c06-45ar-441e-a3d5-94add1fa9658",
                    },
                    "selfUri": "/api/v2/workforcemanagement/businessunits/1f271csd-ff47-4ead-8343-323ac1751ed6",
                }
            ]
        },
    )

    result = api.get_business_units(access_token, region)
    throttle.wait.assert_called_once()
    cli.print_info.assert_called_once_with("Sending request for business units.")
    cli.print_status.assert_called_once_with(f"Successfully received 1 business units.")
    assert result == [BusinessUnit("1f271csd-ff47-4ead-8343-323ac1751ed6", "Test BU")]


def test_skip_bu_no_name_response(
    api, network_client, throttle, cli, region, access_token
):
    network_client.execute.return_value = NetworkResponse(
        ok=True,
        status=200,
        data={
            "entities": [
                {
                    "id": "1f271csd-ff47-4ead-8343-323ac1751ed6",
                    "name": "Test BU",
                    "authorized": False,
                    "division": {
                        "id": "0c1a7c06-45ar-441e-a3d5-94add1fa9658",
                        "selfUri": "/api/v2/authorization/divisions/0c1a7c06-45ar-441e-a3d5-94add1fa9658",
                    },
                    "selfUri": "/api/v2/workforcemanagement/businessunits/1f271csd-ff47-4ead-8343-323ac1751ed6",
                },
                {
                    "id": "1f271csd-aa47-4ead-8343-323ac1751ed6",
                    "name": "",
                    "authorized": False,
                    "division": {
                        "id": "0c1a7c06-45ar-441e-a3d5-94add1fa9658",
                        "selfUri": "/api/v2/authorization/divisions/0c1a7c06-45ar-441e-a3d5-94add1fa9658",
                    },
                    "selfUri": "/api/v2/workforcemanagement/businessunits/1f271csd-aa47-4ead-8343-323ac1751ed6",
                },
            ]
        },
    )

    result = api.get_business_units(access_token, region)
    throttle.wait.assert_called_once()
    cli.print_info.assert_called_once_with("Sending request for business units.")
    cli.print_info.assert_called_once_with("Sending request for business units.")
    cli.print_status.assert_called_once_with(f"Successfully received 1 business units.")
    cli.print_warn.assert_called_once_with(
        f"Skipping BU - 1f271csd-aa47-4ead-8343-323ac1751ed6 as it doesnt have a name"
    )
    assert result == [BusinessUnit("1f271csd-ff47-4ead-8343-323ac1751ed6", "Test BU")]


def test_skip_bu_no_id_response(
    api, network_client, throttle, cli, region, access_token
):
    network_client.execute.return_value = NetworkResponse(
        ok=True,
        status=200,
        data={
            "entities": [
                {
                    "id": "1f271csd-ff47-4ead-8343-323ac1751ed6",
                    "name": "Test BU",
                    "authorized": False,
                    "division": {
                        "id": "0c1a7c06-45ar-441e-a3d5-94add1fa9658",
                        "selfUri": "/api/v2/authorization/divisions/0c1a7c06-45ar-441e-a3d5-94add1fa9658",
                    },
                    "selfUri": "/api/v2/workforcemanagement/businessunits/1f271csd-ff47-4ead-8343-323ac1751ed6",
                },
                {
                    "id": "",
                    "name": "Test BU 2",
                    "authorized": False,
                    "division": {
                        "id": "0c1a7c06-45ar-441e-a3d5-94add1fa9658",
                        "selfUri": "/api/v2/authorization/divisions/0c1a7c06-45ar-441e-a3d5-94add1fa9658",
                    },
                    "selfUri": "/api/v2/workforcemanagement/businessunits/1f271csd-aa47-4ead-8343-323ac1751ed6",
                },
            ]
        },
    )

    result = api.get_business_units(access_token, region)
    throttle.wait.assert_called_once()
    cli.print_info.assert_called_once_with("Sending request for business units.")
    cli.print_info.assert_called_once_with("Sending request for business units.")
    cli.print_status.assert_called_once_with(f"Successfully received 1 business units.")
    cli.print_warn.assert_called_once_with(
        f"Skipping BU - Test BU 2 as it doesnt have an id"
    )
    assert result == [BusinessUnit("1f271csd-ff47-4ead-8343-323ac1751ed6", "Test BU")]


@pytest.mark.parametrize("payload", [None, {}])
def test_skip_bu_no_data_response(
    api, network_client, throttle, cli, region, access_token, payload
):
    network_client.execute.return_value = NetworkResponse(
        ok=True,
        status=200,
        data=payload,
    )

    with pytest.raises(NetworkResponseException) as exc_info:
        api.get_business_units(access_token, region)

    throttle.wait.assert_called_once()
    cli.print_info.assert_called_once_with("Sending request for business units.")
    cli.print_error.assert_called_once_with(
        "No Business Units were included in the response."
    )
    error = exc_info.value
    assert str(error) == "No Business Units were included in the response."
    assert error.status == 200
    assert error.data == payload
