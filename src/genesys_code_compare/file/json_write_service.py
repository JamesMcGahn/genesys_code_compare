from __future__ import annotations
from typing import Any


from pathlib import Path
import json

from ..cli import CLI
from .base_write import BaseWrite


class JSONFileService(BaseWrite):

    def __init__(self, cli: CLI):
        super().__init__(cli)

    def write(self, data: dict[str, Any] | list[Any], output_path: str | Path) -> Path:

        try:
            output_path = self.get_output_path(output_path, file_ext=".json")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)
            message = f"File Successfully saved {output_path}"
            self._cli.print_status(message)
            return output_path
        except OSError:
            message = f"Could not save the file {output_path}"
            self._cli.print_error(message)
            raise

        except Exception:
            message = f"Unexpected error saving the file {output_path}"
            self._cli.print_error(message)
            raise
