import json
from unittest.mock import Mock

import pytest

from genesys_code_compare.cli import CLI
from genesys_code_compare.file.raw_payload_service import RawPlayloadService
from genesys_code_compare.models.genesys import BusinessUnit


@pytest.mark.parametrize(("name", "safe_name"), [
    ("Medicaid Enrollment Growth NY", "Medicaid Enrollment Growth NY"),
    ('NY<>:"/\\|?*\x00\x1f', "NY" + "_" * 11),
    ("  NY...  ", "NY"),
    (" . ", "business_unit"),
    ("x" * 150, "x" * 100),
    ("CON.sales", "CON.sales"),
])
def test_payload_filename_and_body(tmp_path, name, safe_name):
    payload = {"entities": [{"name": "Bereavement ", "active": False}]}
    bu = BusinessUnit("id-1", name, raw_payload=payload)
    report = tmp_path / "run" / "report.xlsx"

    RawPlayloadService(Mock(spec=CLI)).write_payloads([bu], report)

    files = list(report.parent.iterdir())
    assert files == [report.parent / f"bu_{safe_name}_id-1.json"]
    assert json.loads(files[0].read_text()) == payload
    assert not report.exists()


def test_missing_payload_is_skipped_but_empty_payload_is_saved(tmp_path):
    cli = Mock(spec=CLI)
    units = [BusinessUnit("missing", "Missing"),
             BusinessUnit("empty", "Empty", raw_payload={})]

    RawPlayloadService(cli).write_payloads(units, tmp_path / "report.xlsx")

    assert [p.name for p in tmp_path.iterdir()] == ["bu_Empty_empty.json"]
    assert json.loads((tmp_path / "bu_Empty_empty.json").read_text()) == {}
    cli.print_warn.assert_called_once()


def test_ids_distinguish_names_that_sanitize_identically(tmp_path):
    units = [BusinessUnit("a", "NY/Team", raw_payload={"source": "a"}),
             BusinessUnit("b", "NY:Team", raw_payload={"source": "b"})]

    RawPlayloadService(Mock(spec=CLI)).write_payloads(units, tmp_path / "report.xlsx")

    for identifier in ("a", "b"):
        path = tmp_path / f"bu_NY_Team_{identifier}.json"
        assert json.loads(path.read_text()) == {"source": identifier}


def test_separate_run_folders_preserve_previous_payload(tmp_path):
    service = RawPlayloadService(Mock(spec=CLI))
    for run in ("first", "second"):
        service.write_payloads(
            [BusinessUnit("id", "NY", raw_payload={"run": run})],
            tmp_path / run / "report.xlsx",
        )
    for run in ("first", "second"):
        assert json.loads((tmp_path / run / "bu_NY_id.json").read_text()) == {"run": run}
