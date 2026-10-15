from genesys_code_compare.config import get_config_path
from pathlib import Path


def test_get_external_config():
    project_root = Path(__file__).resolve().parents[1]
    expected = project_root / "config.toml"

    assert get_config_path() == expected


def test_get_default_config():
    project_root = Path(__file__).resolve().parents[1]
    external_file = project_root / "config.toml"

    try:
        if external_file.exists():
            external_file.rename("./__test_config.toml")
            print("renamed - config to __test_config for testing.")

        assert (
            project_root / "src" / "genesys_code_compare" / "default_config.toml"
            == get_config_path()
        )
    finally:
        renamed_file = project_root / "__test_config.toml"
        if renamed_file.exists():
            renamed_file.rename("config.toml")
            print("renamed - config back to correct name.")
