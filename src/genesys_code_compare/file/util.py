import sys
from pathlib import Path


class FileUtil:
    @staticmethod
    def get_app_directory() -> Path:
        if getattr(sys, "frozen", False):

            return Path(sys.executable).resolve().parent

        return Path.cwd()
