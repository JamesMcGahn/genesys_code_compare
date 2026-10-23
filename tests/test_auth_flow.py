from unittest.mock import Mock, call

import pytest

from genesys_code_compare.errors.network import (
    NotAuthenticatedException,
)
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
def gen_session():
    return Mock(spec=GenesysSession)


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


def test_not_authenticated(
    auth_flow, api, prompts, cli, credentials, region, access_token
):
    corrected = ClientCredentials("corrected-client", "corrected-secret")
    prompts.enter_client_credentials.side_effect = [
        credentials,
        corrected,
    ]
    prompts.prompt_user_for_region.return_value = region

    api.authenticate.side_effect = [
        NotAuthenticatedException(),
        access_token,
    ]

    session = auth_flow.run()

    assert session.region == region
    assert api.authenticate.call_args_list == [
        call(credentials, region),
        call(corrected, region),
    ]
    cli.print_error.assert_called_once_with(
        "Authentication failed. Check your client ID, client secret, and region. Try again."
    )


def test_expected_response(
    auth_flow, api, prompts, cli, credentials, region, access_token, gen_session
):
    prompts.enter_client_credentials.return_value = credentials
    prompts.prompt_user_for_region.return_value = region
    api.authenticate.return_value = access_token
    session = auth_flow.run()
    assert session.region == region
    assert session._token == access_token
    api.authenticate.assert_called_once_with(credentials, region)
    cli.print_error.assert_not_called()
