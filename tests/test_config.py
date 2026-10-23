from pathlib import Path
import pytest
from genesys_code_compare.errors import ConfigError
from genesys_code_compare.models.genesys import Region
import tomllib
from unittest.mock import Mock

from genesys_code_compare.app_config import AppConfig
from genesys_code_compare.cli import CLI


@pytest.fixture
def cli():
    return Mock(spec=CLI)


@pytest.fixture
def app_config(cli):
    return AppConfig(cli)


def test_get_default_path(app_config):
    project_root = Path(__file__).resolve().parents[1]
    package_folder = project_root / "src" / "genesys_code_compare"
    assert package_folder / "default_config.toml" == app_config.get_default_config()


def test_get_external_config(app_config):
    project_root = Path(__file__).resolve().parents[1]
    expected = project_root / "config.toml"

    assert app_config.get_config_path() == expected


def test_get_default_config(app_config):
    project_root = Path(__file__).resolve().parents[1]
    package_folder = project_root / "src" / "genesys_code_compare"
    assert package_folder / "default_config.toml" == app_config.get_config_path(
        package_folder
    )


def test_missing_config_file(tmp_path, app_config):
    missing_file = tmp_path / "missing.toml"

    with pytest.raises(ConfigError, match="does NOT exist"):
        app_config.load_config(missing_file)


def test_valid_toml(tmp_path, app_config):
    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[regions.us_east]
login_url = "https://login.mypurecloud.com"
api_url = "https://api.mypurecloud.com"
""")

    app_config.load_config(config_file)
    result = app_config.region_list
    assert result == [
        Region(
            name="us_east",
            login_url="https://login.mypurecloud.com",
            api_url="https://api.mypurecloud.com",
        )
    ]


def test_load_with_no_regions(tmp_path, app_config):
    config_file = tmp_path / "config.toml"
    config_file.write_text("""""")

    with pytest.raises(ConfigError, match="Config file doesn't have any regions"):
        app_config.load_config(config_file)


def test_load_with_no_login_url(tmp_path, app_config):
    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[regions.us_east]
api_url = "https://api.mypurecloud.com"
""")

    with pytest.raises(ConfigError, match="No Region exist"):
        app_config.load_config(config_file)


def test_load_with_no_api_url(tmp_path, app_config):
    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[regions.us_east]
login_url = "https://login.mypurecloud.com"
""")

    with pytest.raises(ConfigError, match="No Region exist"):
        app_config.load_config(config_file)


def test_load_not_formatted(tmp_path, app_config):
    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[regions]
login_url = "https://login.mypurecloud.com"
""")

    with pytest.raises(ConfigError, match="formatted improperly"):
        app_config.load_config(config_file)


def test_load_not_invalid_toml(tmp_path, app_config):
    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[regions
login_url = "https://login.mypurecloud.com"
""")

    with pytest.raises(tomllib.TOMLDecodeError):
        app_config.load_config(config_file)


def test_load_no_file(tmp_path, app_config):
    config_file = tmp_path / "config.toml"

    with pytest.raises(ConfigError, match="Config file does NOT exist."):
        app_config.load_config(config_file)
