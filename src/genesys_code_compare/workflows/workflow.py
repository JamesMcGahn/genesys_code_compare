from typing import Protocol


class Workflow(Protocol):
    def run(self) -> None: ...
