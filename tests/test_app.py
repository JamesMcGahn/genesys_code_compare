from unittest.mock import Mock, call

import pytest

from genesys_code_compare.app import App
from genesys_code_compare.cli import CLI
from genesys_code_compare.prompts import Prompts
from genesys_code_compare.genesys import GenesysAPI
from genesys_code_compare.app_config import AppConfig
from genesys_code_compare.enums import RUN_MENU
from genesys_code_compare.analyze import ActivityCodeAnalyze
from genesys_code_compare.file import AnalyzeSheetService
from genesys_code_compare.workflows import CompareActivityCodes
from genesys_code_compare.workflows import AuthFlow
from genesys_code_compare.genesys import GenesysSession
from genesys_code_compare.errors.network import (
    NetworkResponseException,
    RetryableNetworkException,
)


@pytest.fixture
def app():
    instance = App()

    instance.cli = Mock(spec=CLI)
    instance.prompts = Mock(spec=Prompts)
    instance._app_config = Mock(spec=AppConfig)
    instance._gen_api = Mock(spec=GenesysAPI)
    instance.activity_code_analyzer = Mock(spec=ActivityCodeAnalyze)
    instance.activity_code_reports = Mock(spec=AnalyzeSheetService)

    yield instance

    instance._http_session.close()


def test_startup(app):
    app.start_up()

    app._app_config.load_config.assert_called_once_with()
    app.prompts.welcome_message.assert_called_once_with()


def test_app_exited(app):
    app.prompts.welcome_menu.return_value = RUN_MENU.QUIT

    with pytest.raises(SystemExit) as exc_info:
        app.run()
    app._app_config.load_config.assert_called_once_with()
    app.prompts.welcome_menu.assert_called_once()
    assert exc_info.value.code == 0


def test_app_runs_comparison(app, monkeypatch):
    auth_flow = Mock(spec=AuthFlow)
    auth_flow.run.return_value = Mock(spec=GenesysSession)

    monkeypatch.setattr(
        "genesys_code_compare.app.AuthFlow",
        Mock(return_value=auth_flow),
    )

    workflow = Mock(spec=CompareActivityCodes)
    monkeypatch.setattr(
        "genesys_code_compare.app.CompareActivityCodes",
        Mock(return_value=workflow),
    )

    app.prompts.welcome_menu.side_effect = [
        RUN_MENU.COMPARE_ACTIVITY_CODES,
        RUN_MENU.QUIT,
    ]

    with pytest.raises(SystemExit) as exc_info:
        app.run()

    assert exc_info.value.code == 0
    workflow.run.assert_called_once_with()
    assert app.prompts.welcome_menu.call_count == 2


def test_app_runs_comparison_twice(app, monkeypatch):
    auth_flow = Mock(spec=AuthFlow)
    auth_flow.run.return_value = Mock(spec=GenesysSession)

    monkeypatch.setattr(
        "genesys_code_compare.app.AuthFlow",
        Mock(return_value=auth_flow),
    )

    workflow = Mock(spec=CompareActivityCodes)
    monkeypatch.setattr(
        "genesys_code_compare.app.CompareActivityCodes",
        Mock(return_value=workflow),
    )

    app.prompts.welcome_menu.side_effect = [
        RUN_MENU.COMPARE_ACTIVITY_CODES,
        RUN_MENU.COMPARE_ACTIVITY_CODES,
        RUN_MENU.QUIT,
    ]

    with pytest.raises(SystemExit) as exc_info:
        app.run()

    assert exc_info.value.code == 0
    assert workflow.run.call_count == 2
    assert app.prompts.welcome_menu.call_count == 3


@pytest.mark.parametrize(
    ("error", "msg"),
    [
        (
            RetryableNetworkException,
            "Genesys is temporarily unavailable or rate limiting requests. Wait before trying again.",
        ),
        (
            NetworkResponseException(status=0),
            "Cannot reach Genesys. Check your connection.",
        ),
        (
            NetworkResponseException(status=403),
            "Access denied. Check the client's permissions.",
        ),
        (
            NetworkResponseException(status=405, message="test"),
            "Genesys request failed: test",
        ),
        (
            PermissionError,
            "Cannot write the report. Close it in Excel and check the output folder's permissions.",
        ),
        (
            OSError("test"),
            "Cannot save the report: test",
        ),
    ],
)
def test_app_errors(app, error, msg, monkeypatch):
    auth_flow = Mock(spec=AuthFlow)
    auth_flow.run.return_value = Mock(spec=GenesysSession)

    monkeypatch.setattr(
        "genesys_code_compare.app.AuthFlow",
        Mock(return_value=auth_flow),
    )

    workflow = Mock(spec=CompareActivityCodes)
    workflow.run.side_effect = error

    monkeypatch.setattr(
        "genesys_code_compare.app.CompareActivityCodes",
        Mock(return_value=workflow),
    )

    app.prompts.welcome_menu.side_effect = [
        RUN_MENU.COMPARE_ACTIVITY_CODES,
        RUN_MENU.QUIT,
    ]

    with pytest.raises(SystemExit) as exc_info:
        app.run()

    assert exc_info.value.code == 0
    workflow.run.assert_called_once_with()

    app.cli.print_error.assert_called_once_with(msg)
    assert app.prompts.welcome_menu.call_count == 2


def test_app_recovers_after_failed_comparison(app, monkeypatch):
    auth_flow = Mock(spec=AuthFlow)
    auth_flow.run.return_value = Mock(spec=GenesysSession)

    monkeypatch.setattr(
        "genesys_code_compare.app.AuthFlow",
        Mock(return_value=auth_flow),
    )

    workflow = Mock(spec=CompareActivityCodes)
    workflow.run.side_effect = [
        NetworkResponseException(status=0),
        None,
    ]

    monkeypatch.setattr(
        "genesys_code_compare.app.CompareActivityCodes",
        Mock(return_value=workflow),
    )

    app.prompts.welcome_menu.side_effect = [
        RUN_MENU.COMPARE_ACTIVITY_CODES,
        RUN_MENU.COMPARE_ACTIVITY_CODES,
        RUN_MENU.QUIT,
    ]

    with pytest.raises(SystemExit) as exc_info:
        app.run()

    assert exc_info.value.code == 0
    assert workflow.run.call_args_list == [call(), call()]
    assert app.prompts.welcome_menu.call_count == 3
    app.cli.print_error.assert_called_once_with(
        "Cannot reach Genesys. Check your connection."
    )


def test_app_unexpected_error_propagates(app, monkeypatch):
    auth_flow = Mock(spec=AuthFlow)
    auth_flow.run.return_value = Mock(spec=GenesysSession)

    monkeypatch.setattr(
        "genesys_code_compare.app.AuthFlow",
        Mock(return_value=auth_flow),
    )

    workflow = Mock(spec=CompareActivityCodes)
    error = TypeError("Unexpected programming error")
    workflow.run.side_effect = error

    monkeypatch.setattr(
        "genesys_code_compare.app.CompareActivityCodes",
        Mock(return_value=workflow),
    )

    app.prompts.welcome_menu.side_effect = [
        RUN_MENU.COMPARE_ACTIVITY_CODES,
        RUN_MENU.QUIT,
    ]

    with pytest.raises(TypeError) as exc_info:
        app.run()

    assert exc_info.value is error
    workflow.run.assert_called_once_with()
    app.prompts.welcome_menu.assert_called_once_with()
    app.cli.print_error.assert_not_called()
