from datetime import datetime
from unittest.mock import Mock

from genesys_code_compare.file.base_write import BaseWrite
from genesys_code_compare.file.util import FileUtil


def test_generated_paths_separate_runs_within_same_second(tmp_path, monkeypatch):
    clock = Mock()
    clock.now.side_effect = [
        datetime(2026, 11, 3, 13, 48, 40, 1),
        datetime(2026, 11, 3, 13, 48, 40, 2),
    ]
    monkeypatch.setattr("genesys_code_compare.file.base_write.datetime", clock)
    monkeypatch.setattr(FileUtil, "get_app_directory", lambda: tmp_path)
    service = BaseWrite(Mock())

    first = service.get_output_path(file_name="compare_codes", file_ext=".json")
    second = service.get_output_path(file_name="compare_codes", file_ext=".json")

    assert first == (tmp_path / "reports" / "20261103-134840-000001"
                     / "report_compare_codes_20261103-134840-000001.json")
    assert first.parent != second.parent
    assert second.suffix == ".json"


def test_explicit_path_is_preserved(tmp_path):
    path = tmp_path / "chosen.json"
    assert BaseWrite(Mock()).get_output_path(str(path), file_name="ignored") == path
