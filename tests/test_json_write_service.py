import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from genesys_code_compare.cli import CLI
from genesys_code_compare.file.json_write_service import JSONFileService


@pytest.mark.parametrize("as_string", [False, True])
@pytest.mark.parametrize("payload", [
    {"entities": [{"name": "Bereavement ", "active": False, "note": "Québec"}],
     "extra": {"value": None}},
    [{"name": "Lunch"}, 1, True, None],
    {},
    [],
])
def test_write_round_trips_payload_and_returns_path(tmp_path, payload, as_string):
    cli = Mock(spec=CLI)
    path = tmp_path / "new" / "nested" / "payload.json"

    result = JSONFileService(cli).write(payload, str(path) if as_string else path)

    assert result == path
    assert json.loads(path.read_text(encoding="utf-8")) == payload
    cli.print_status.assert_called_once()
    cli.print_error.assert_not_called()


@pytest.mark.parametrize("operation", ["mkdir", "open"])
def test_filesystem_error_is_preserved(tmp_path, monkeypatch, operation):
    cli = Mock(spec=CLI)
    error = PermissionError(13, "Access denied", str(tmp_path / "payload.json"))
    monkeypatch.setattr(Path, operation, Mock(side_effect=error))

    with pytest.raises(PermissionError) as caught:
        JSONFileService(cli).write({}, tmp_path / "payload.json")

    assert caught.value is error
    cli.print_error.assert_called_once()
    cli.print_status.assert_not_called()


def test_serialization_error_keeps_specific_exception(tmp_path):
    cli = Mock(spec=CLI)
    with pytest.raises(TypeError, match="not JSON serializable"):
        JSONFileService(cli).write({"invalid": object()}, tmp_path / "payload.json")
    cli.print_error.assert_called_once()
    cli.print_status.assert_not_called()
