from pathlib import Path
import sys
import tomllib


def get_config_path() -> Path:
    if getattr(sys, "frozen", False):
        external_dir = Path(sys.executable).resolve().parent
    else:
        external_dir = Path(__file__).resolve().parents[2]

    default_config = Path(__file__).resolve().with_name("default_config.toml")
    external_config = external_dir / "config.toml"

    path = external_config if external_config.exists() else default_config
    return path


def load_config() -> dict:
    with get_config_path().open("rb") as file:
        return tomllib.load(file)
