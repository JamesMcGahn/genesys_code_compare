from genesys_code_compare.config import get_config_path, get_default_config, load_config
from pathlib import Path
import pytest
from genesys_code_compare.errors import ConfigError
from genesys_code_compare.models.config import Regions
import tomllib


def test_get_default_path():
    project_root = Path(__file__).resolve().parents[1]
    package_folder = project_root / "src" / "genesys_code_compare"
    assert package_folder / "default_config.toml" == get_default_config()


def test_get_external_config():
    project_root = Path(__file__).resolve().parents[1]
    expected = project_root / "config.toml"

    assert get_config_path() == expected


def test_get_default_config():
    project_root = Path(__file__).resolve().parents[1]
    package_folder = project_root / "src" / "genesys_code_compare"
    assert package_folder / "default_config.toml" == get_config_path(package_folder)


def test_missing_config_file(tmp_path):
    missing_file = tmp_path / "missing.toml"

    with pytest.raises(ConfigError, match="does NOT exist"):
        load_config(missing_file)


def test_valid_toml(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[regions.us_east]
login_url = "https://login.mypurecloud.com"
api_url = "https://api.mypurecloud.com"
""")

    result = load_config(config_file)
    assert result == [
        Regions(
            name="us_east",
            login_url="https://login.mypurecloud.com",
            api_url="https://api.mypurecloud.com",
        )
    ]


def test_load_with_no_regions(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text("""""")

    with pytest.raises(ConfigError, match="Config file doesn't have any regions"):
        load_config(config_file)


def test_load_with_no_regions(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text("""""")

    with pytest.raises(ConfigError, match="Config file doesn't have any regions"):
        load_config(config_file)


def test_load_with_no_login_url(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[regions.us_east]
api_url = "https://api.mypurecloud.com"
""")

    with pytest.raises(ConfigError, match="No Regions exist"):
        load_config(config_file)


def test_load_with_no_api_url(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[regions.us_east]
login_url = "https://login.mypurecloud.com"
""")

    with pytest.raises(ConfigError, match="No Regions exist"):
        load_config(config_file)


def test_load_not_formatted(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[regions]
login_url = "https://login.mypurecloud.com"
""")

    with pytest.raises(ConfigError, match="formatted improperly"):
        load_config(config_file)


def test_load_not_invalid_toml(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[regions
login_url = "https://login.mypurecloud.com"
""")

    with pytest.raises(tomllib.TOMLDecodeError):
        load_config(config_file)


def test_load_no_file(tmp_path):
    config_file = tmp_path / "config.toml"

    with pytest.raises(ConfigError, match="Config file does NOT exist."):
        load_config(config_file)
