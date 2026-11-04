from pathlib import Path


from .util import FileUtil
from datetime import datetime
from ..cli import CLI


class BaseWrite:
    def __init__(self, cli: CLI):
        self._cli = cli

    def write(self):
        raise NotImplementedError(
            f"{self.__class__.__name__}: has not implemented write method"
        )

    def get_output_path(
        self,
        output_path: str | Path | None = None,
        file_name: str = "",
        file_ext: str = ".xlsx",
    ) -> Path:
        if output_path is not None:
            return Path(output_path)
        now = datetime.now()
        timestamp_str = now.strftime("%Y%m%d-%H%M%S-%f")
        return (
            FileUtil.get_app_directory()
            / "reports"
            / timestamp_str
            / f"report_{file_name}_{timestamp_str}{file_ext}"
        )
