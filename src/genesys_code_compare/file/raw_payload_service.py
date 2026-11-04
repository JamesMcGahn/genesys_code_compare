from .json_write_service import JSONFileService
from ..cli import CLI
from pathlib import Path
from ..models.genesys import BusinessUnit
import re


class RawPlayloadService(JSONFileService):

    def __init__(self, cli: CLI):
        super().__init__(cli)

    def write_payloads(
        self, business_units: list[BusinessUnit], output_path: Path
    ) -> None:
        folder = output_path.parent
        for bu in business_units:
            if bu.raw_payload is None:
                self._cli.print_warn(
                    f"Skipping writing payload for {bu.name} as payload is None."
                )
                continue

            safe_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", bu.name)
            safe_name = safe_name.strip().rstrip(". ")[:100].rstrip(". ")
            safe_name = safe_name or "business_unit"
            output_path = folder / f"bu_{safe_name}_{bu.bu_id}.json"
            self.write(bu.raw_payload, output_path)
