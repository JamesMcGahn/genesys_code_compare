from unittest.mock import Mock

import pytest

from genesys_code_compare.cli import CLI
from genesys_code_compare.enums import RUN_MENU
from genesys_code_compare.models.genesys import (
    BusinessUnit,
    ClientCredentials,
    Region,
)
from genesys_code_compare.prompts import Prompts


@pytest.fixture
def cli():
    return Mock(spec=CLI)


@pytest.fixture
def prompts(cli):
    return Prompts(cli)


@pytest.fixture
def regions():
    return [
        Region("Region A", "https://login-a.example", "https://api-a.example"),
        Region("Region B", "https://login-b.example", "https://api-b.example"),
    ]


@pytest.fixture
def business_units():
    # Deliberately unsorted to verify display ordering.
    return [
        BusinessUnit("b", "BU B"),
        BusinessUnit("a", "BU A"),
        BusinessUnit("c", "BU C"),
    ]


@pytest.mark.parametrize("choice", list(RUN_MENU))
def test_welcome_menu_returns_selected_option(prompts, cli, choice):
    cli.select.return_value = choice.value

    result = prompts.welcome_menu()

    assert result is choice
    cli.select.assert_called_once_with(
        "Select : ",
        [RUN_MENU.COMPARE_ACTIVITY_CODES, RUN_MENU.QUIT],
    )


def test_welcome_menu_cancellation(prompts, cli):
    cli.select.return_value = None

    with pytest.raises(KeyboardInterrupt):
        prompts.welcome_menu()


def test_credentials_returns_entered_values(prompts, cli):
    cli.text_input.return_value = "client"
    cli.password_input.return_value = "secret"

    result = prompts.enter_client_credentials()

    assert result == ClientCredentials("client", "secret")
    cli.text_input.assert_called_once_with("Enter the Client ID: ")
    cli.password_input.assert_called_once_with("Enter the Client Secret: ")


def test_empty_credentials_prompt_again(prompts, cli):
    cli.text_input.side_effect = ["", "client"]
    cli.password_input.side_effect = ["", "secret"]

    result = prompts.enter_client_credentials()

    assert result == ClientCredentials("client", "secret")
    assert cli.text_input.call_count == 2
    assert cli.password_input.call_count == 2


def test_credentials_are_trimmed(prompts, cli):
    cli.text_input.return_value = "  client "
    cli.password_input.return_value = "  secret "

    result = prompts.enter_client_credentials()

    assert result == ClientCredentials("client", "secret")


def test_whitespace_only_credentials_prompt_again(prompts, cli):
    cli.text_input.side_effect = ["   ", "client"]
    cli.password_input.side_effect = ["   ", "secret"]

    result = prompts.enter_client_credentials()

    assert result == ClientCredentials("client", "secret")
    assert cli.text_input.call_count == 2
    assert cli.password_input.call_count == 2


@pytest.mark.parametrize("cancel_at", ["client_id", "client_secret"])
def test_credentials_cancellation(prompts, cli, cancel_at):
    cli.text_input.return_value = None if cancel_at == "client_id" else "client"
    cli.password_input.return_value = None

    with pytest.raises(KeyboardInterrupt):
        prompts.enter_client_credentials()

    cli.text_input.assert_called_once()
    if cancel_at == "client_id":
        cli.password_input.assert_not_called()
    else:
        cli.password_input.assert_called_once()


def test_region_selection_returns_matching_object(prompts, cli, regions):
    cli.select.return_value = "Region B"

    result = prompts.prompt_user_for_region(regions)

    assert result is regions[1]
    cli.select.assert_called_once()

    question, choices = cli.select.call_args.args
    assert question == "Select region: "
    assert [(choice.title, choice.value) for choice in choices] == [
        ("Region A", "Region A"),
        ("Region B", "Region B"),
    ]


def test_region_cancellation(prompts, cli, regions):
    cli.select.return_value = None

    with pytest.raises(KeyboardInterrupt):
        prompts.prompt_user_for_region(regions)


def test_unknown_region_selection(prompts, cli, regions):
    cli.select.return_value = "Unknown"

    with pytest.raises(
        RuntimeError,
        match="Selected region was not found: Unknown",
    ):
        prompts.prompt_user_for_region(regions)


def test_business_unit_selection_maps_ids(prompts, cli, business_units):
    cli.checkbox.return_value = ["a", "c"]

    result = prompts.prompt_user_for_bus(business_units)

    assert result == [business_units[1], business_units[2]]
    cli.print_warn.assert_not_called()


def test_business_unit_choices_are_sorted(prompts, cli, business_units):
    cli.checkbox.return_value = ["a"]

    prompts.prompt_user_for_bus(business_units)

    cli.checkbox.assert_called_once()
    question, choices = cli.checkbox.call_args.args

    assert question == "Select BUs:"
    assert [(choice.title, choice.value) for choice in choices] == [
        ("BU A", "a"),
        ("BU B", "b"),
        ("BU C", "c"),
    ]


def test_empty_business_unit_selection_retries(prompts, cli, business_units):
    cli.checkbox.side_effect = [[], ["a"]]

    result = prompts.prompt_user_for_bus(business_units)

    assert result == [business_units[1]]
    assert cli.checkbox.call_count == 2
    cli.print_warn.assert_called_once_with(
        "Please <space> to select and then <enter>. "
        "If you want to exit, press ctrl+c."
    )


def test_business_unit_selection_cancellation(prompts, cli, business_units):
    cli.checkbox.return_value = None

    with pytest.raises(KeyboardInterrupt):
        prompts.prompt_user_for_bus(business_units)

    cli.checkbox.assert_called_once()
    cli.print_warn.assert_not_called()
