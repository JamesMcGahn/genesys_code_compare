from unittest.mock import Mock, call

import pytest

from genesys_code_compare.errors.network import (
    NotAuthenticatedException,
    NetworkResponseException,
)
from genesys_code_compare.genesys import GenesysAPI, GenesysSession
from genesys_code_compare.models.genesys import (
    ClientCredentials,
    BusinessUnit,
    ActivityCode,
    Region,
)
from genesys_code_compare.models.network import AccessToken
from genesys_code_compare.cli import CLI
from dataclasses import replace
from genesys_code_compare.workflows.compare_activity_codes import CompareActivityCodes
from genesys_code_compare.analyze import ActivityCodeAnalyze
from genesys_code_compare.file import AnalyzeSheetService
from genesys_code_compare.prompts import Prompts
from genesys_code_compare.models.analyze import CodePresence, MatchResult


@pytest.fixture
def cli():
    return Mock(spec=CLI)


@pytest.fixture
def api():
    return Mock(spec=GenesysAPI)


@pytest.fixture
def gen_session():
    return Mock(spec=GenesysSession)


@pytest.fixture
def analyze():
    return Mock(spec=ActivityCodeAnalyze)


@pytest.fixture
def sheet_writer():
    return Mock(spec=AnalyzeSheetService)


@pytest.fixture
def prompts():
    return Mock(spec=Prompts)


@pytest.fixture
def compare_act_codes(cli, api, gen_session, prompts, analyze, sheet_writer):
    return CompareActivityCodes(cli, api, gen_session, prompts, analyze, sheet_writer)


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


def test_comparison_passes_data_through_workflow(
    compare_act_codes,
    cli,
    api,
    gen_session,
    prompts,
    analyze,
    sheet_writer,
    access_token,
    region,
    business_unit,
    tmp_path,
):
    code = ActivityCode("123", "test", True, "test", True)
    match_value = MatchResult(
        exact_name_matches=[CodePresence("test", {business_unit.name: code}, [])]
    )
    output_path = tmp_path / "report.xlsx"

    gen_session.get_valid_token.return_value = access_token
    gen_session.region = region
    api.get_business_units.return_value = [business_unit]

    populated_bu = replace(business_unit, activity_codes=(code,))
    api.get_business_unit_activity_codes.return_value = populated_bu
    prompts.prompt_user_for_bus.return_value = [business_unit]
    analyze.analyze.return_value = match_value
    sheet_writer.get_output_path.return_value = output_path

    compare_act_codes.run()

    gen_session.get_valid_token.assert_called_once()
    api.get_business_units.assert_called_once_with(access_token, region)
    api.get_business_unit_activity_codes.assert_called_once_with(
        access_token, region, business_unit
    )

    prompts.prompt_user_for_bus.assert_called_once_with([business_unit])
    analyze.analyze.assert_called_once_with([populated_bu])
    sheet_writer.write_analyze.assert_called_once_with(
        [populated_bu], match_value, output_path
    )


def test_only_selected_business_units_are_processed(
    compare_act_codes,
    api,
    gen_session,
    prompts,
    analyze,
    sheet_writer,
    access_token,
    region,
    tmp_path,
):

    bu_a = BusinessUnit("a", "BU A")
    bu_b = BusinessUnit("b", "BU B")
    bu_c = BusinessUnit("c", "BU C")

    populated_a = replace(
        bu_a,
        activity_codes=(ActivityCode("code-a", "Lunch", False, "Break", False),),
    )
    populated_c = replace(
        bu_c,
        activity_codes=(ActivityCode("code-c", "Lunch", False, "Break", False),),
    )

    match_result = MatchResult()
    output_path = tmp_path / "report.xlsx"

    gen_session.get_valid_token.return_value = access_token
    gen_session.region = region

    api.get_business_units.return_value = [bu_a, bu_b, bu_c]
    prompts.prompt_user_for_bus.return_value = [bu_a, bu_c]
    api.get_business_unit_activity_codes.side_effect = [
        populated_a,
        populated_c,
    ]

    analyze.analyze.return_value = match_result
    sheet_writer.get_output_path.return_value = output_path

    compare_act_codes.run()

    # Assert
    prompts.prompt_user_for_bus.assert_called_once_with([bu_a, bu_b, bu_c])

    assert api.get_business_unit_activity_codes.call_args_list == [
        call(access_token, region, bu_a),
        call(access_token, region, bu_c),
    ]

    analyze.analyze.assert_called_once_with([populated_a, populated_c])
    sheet_writer.write_analyze.assert_called_once_with(
        [populated_a, populated_c],
        match_result,
        output_path,
    )


def test_token_failure_stops_comparison(
    compare_act_codes,
    gen_session,
    api,
    prompts,
    analyze,
    sheet_writer,
):
    gen_session.get_valid_token.side_effect = NotAuthenticatedException(
        "Authentication failed"
    )

    with pytest.raises(NotAuthenticatedException):
        compare_act_codes.run()

    gen_session.get_valid_token.assert_called_once()
    api.get_business_units.assert_not_called()
    api.get_business_unit_activity_codes.assert_not_called()
    prompts.prompt_user_for_bus.assert_not_called()
    analyze.analyze.assert_not_called()
    sheet_writer.write_analyze.assert_not_called()


def test_bu_response_fails(
    compare_act_codes,
    gen_session,
    api,
    prompts,
    analyze,
    sheet_writer,
):
    api.get_business_units.side_effect = NetworkResponseException(
        "Authentication failed"
    )
    with pytest.raises(NetworkResponseException):
        compare_act_codes.run()

    gen_session.get_valid_token.assert_called_once()
    api.get_business_units.assert_called_once()
    api.get_business_unit_activity_codes.assert_not_called()
    prompts.prompt_user_for_bus.assert_not_called()
    analyze.analyze.assert_not_called()
    sheet_writer.write_analyze.assert_not_called()


def test_selection_interupted(
    compare_act_codes,
    gen_session,
    api,
    prompts,
    analyze,
    sheet_writer,
):
    prompts.prompt_user_for_bus.side_effect = KeyboardInterrupt
    with pytest.raises(KeyboardInterrupt):
        compare_act_codes.run()

    gen_session.get_valid_token.assert_called_once()
    api.get_business_units.assert_called_once()
    api.get_business_unit_activity_codes.assert_not_called()
    prompts.prompt_user_for_bus.assert_called_once()
    analyze.analyze.assert_not_called()
    sheet_writer.write_analyze.assert_not_called()


def test_bu_fails_midway(
    compare_act_codes, gen_session, api, prompts, analyze, sheet_writer, business_unit
):
    code = ActivityCode("123", "test", True, "test", True)
    populated_bu = replace(business_unit, activity_codes=(code,))
    second_bu = BusinessUnit("second-id", "Second BU")
    prompts.prompt_user_for_bus.return_value = [business_unit, second_bu]
    api.get_business_unit_activity_codes.side_effect = [
        populated_bu,
        NetworkResponseException,
    ]
    with pytest.raises(NetworkResponseException):
        compare_act_codes.run()

    gen_session.get_valid_token.assert_called_once()
    api.get_business_units.assert_called_once()
    assert api.get_business_unit_activity_codes.call_count == 2
    prompts.prompt_user_for_bus.assert_called_once()
    analyze.analyze.assert_not_called()
    sheet_writer.write_analyze.assert_not_called()


def test_writer_fails(
    compare_act_codes, gen_session, api, prompts, analyze, sheet_writer, business_unit
):
    prompts.prompt_user_for_bus.return_value = [business_unit]
    sheet_writer.write_analyze.side_effect = PermissionError
    with pytest.raises(PermissionError):
        compare_act_codes.run()

    sheet_writer.write_analyze.assert_called_once()
