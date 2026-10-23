from unittest.mock import Mock

import pytest

import genesys_code_compare


@pytest.mark.parametrize(
    ("run_error", "expected_exception", "exit_code"),
    [
        pytest.param(None, None, None, id="normal-completion"),
        pytest.param(SystemExit(0), SystemExit, 0, id="quit"),
        pytest.param(KeyboardInterrupt(), SystemExit, 130, id="ctrl-c"),
        pytest.param(
            TypeError("Unexpected failure"),
            TypeError,
            None,
            id="unexpected-error",
        ),
    ],
)
def test_main_always_closes_session(
    monkeypatch, run_error, expected_exception, exit_code
):
    app = Mock()
    app.run.side_effect = run_error

    app_constructor = Mock(return_value=app)
    monkeypatch.setattr(
        "genesys_code_compare.App",
        app_constructor,
    )

    if expected_exception is None:
        genesys_code_compare.main()
    else:
        with pytest.raises(expected_exception) as exc_info:
            genesys_code_compare.main()

        if expected_exception is SystemExit:
            assert exc_info.value.code == exit_code

        if not isinstance(run_error, KeyboardInterrupt):
            assert exc_info.value is run_error

    app_constructor.assert_called_once_with()
    app.run.assert_called_once_with()
    app._http_session.close.assert_called_once_with()

    if isinstance(run_error, KeyboardInterrupt):
        app.cli.print_status.assert_called_once_with("Exiting Application.")
    else:
        app.cli.print_status.assert_not_called()
