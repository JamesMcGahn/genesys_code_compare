from pathlib import Path
import sys
import tomllib
from .cli import CLI
from .errors import ConfigError
from .models.config import Region


class AppConfig:
    def __init__(self, cli: CLI):
        self.cli = cli

    def get_default_config(
        self,
    ) -> Path:
        return Path(__file__).resolve().with_name("default_config.toml")

    def get_config_path(self, external_dir: Path | None = None) -> Path:
        if external_dir is None:
            if getattr(sys, "frozen", False):
                external_dir = Path(sys.executable).resolve().parent
            else:
                external_dir = Path(__file__).resolve().parents[2]

        external_config = external_dir / "config.toml"

        path = (
            external_config if external_config.exists() else self.get_default_config()
        )
        return path

    def load_config(self, config_path: Path | None = None) -> list[Region]:
        if config_path is None:
            config_path = self.get_config_path()
        elif not config_path.is_file():
            msg = "Config file does NOT exist."
            self.cli.print_error(msg)
            raise ConfigError(msg)

        with config_path.open("rb") as file:
            config = tomllib.load(file)

            regions: dict[str, str] = config.get("regions")
            if not regions or regions is None:
                msg = "Config file doesn't have any regions. Make sure to write the region like [regions.eu_west]"
                self.cli.print_error(msg)
                raise ConfigError(msg)
            region_list = []
            for k, v in regions.items():
                if not isinstance(v, dict):
                    msg = "Config file is formatted improperly."
                    raise ConfigError(msg)
                login_url = v.get("login_url")
                if not login_url:
                    msg = f"Region - {k} - does NOT have a login url. Skipping..."
                    self.cli.print_error(msg)
                    continue

                api_url = v.get("api_url")
                if not api_url:
                    msg = f"Region - {k} - does NOT have a login url. Skipping..."
                    self.cli.print_error(msg)
                    continue
                region_list.append(Region(name=k, login_url=login_url, api_url=api_url))
            if not region_list:
                msg = "Failed to load config file. No Region exist."
                raise ConfigError(msg)
            return region_list
