from unittest.mock import Mock

import pytest


from genesys_code_compare.genesys import GenesysAPI
from genesys_code_compare.models.genesys import (
    ClientCredentials,
    BusinessUnit,
    Region,
)
from genesys_code_compare.models.network import AccessToken
from genesys_code_compare.network import NetworkClient, NetworkThrottle
from genesys_code_compare.cli import CLI
from genesys_code_compare.prompts import Prompts
from genesys_code_compare.workflows import AuthFlow
from genesys_code_compare.app_config import AppConfig
from genesys_code_compare.genesys.genesys_session import GenesysSession


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
def prompts():
    return Mock(spec=Prompts)


@pytest.fixture
def config():
    return Mock(spec=AppConfig)


@pytest.fixture
def api():
    return Mock(spec=GenesysAPI)


@pytest.fixture
def gen_session(api, credentials, region):
    return GenesysSession(api, credentials, region)


@pytest.fixture
def auth_flow(cli, api, prompts, config):
    return AuthFlow(cli, api, prompts, config)


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


@pytest.fixture
def business_unit():
    return BusinessUnit("1f271csd-ff47-4ead-8343-323ac1751ed6", "Test BU")


@pytest.mark.parametrize("test_field", ["_region", "_credentials"])
def test_region_or_creds_is_none(gen_session, test_field):
    gen_session.__setattr__(test_field, None)

    with pytest.raises(RuntimeError) as exc_info:
        gen_session.get_valid_token()

    error = exc_info.value
    assert str(error) == "Credentials or region is None."


def test_valid_token_expected(gen_session, access_token, monkeypatch, api):
    gen_session._token = access_token
    monkeypatch.setattr(
        "genesys_code_compare.models.network.access_token.time.monotonic",
        lambda: 1000.0,
    )
    token = gen_session.get_valid_token()
    api.authenticate.assert_not_called()
    assert token == access_token


def test_token_is_expired(
    gen_session, access_token, api, monkeypatch, credentials, region
):
    gen_session._token = access_token

    monkeypatch.setattr(
        "genesys_code_compare.models.network.access_token.time.monotonic",
        lambda: 4000.0,
    )

    new_token = AccessToken("new_token", 5000)
    api.authenticate.return_value = new_token

    token = gen_session.get_valid_token()

    api.authenticate.assert_called_once_with(credentials, region)

    assert token is new_token
    assert gen_session._token is new_token


def test_token_is_none(gen_session, api, monkeypatch):
    gen_session._token = None

    monkeypatch.setattr(
        "genesys_code_compare.models.network.access_token.time.monotonic",
        lambda: 4000.0,
    )

    new_token = AccessToken("new_token", 5000)
    api.authenticate.return_value = new_token

    token = gen_session.get_valid_token()

    api.authenticate.assert_called_once()

    assert token is new_token
    assert gen_session._token is new_token
