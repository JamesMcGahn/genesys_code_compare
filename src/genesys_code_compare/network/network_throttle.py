from __future__ import annotations

from typing import TYPE_CHECKING


from time import monotonic, sleep


class NetworkThrottle:
    """Class to throttle requests. Throttle will delay requests based on time of the last request.
    params:
    interval: time between requests in seconds
    """

    def __init__(self, interval: float = 0.5):
        super().__init__()
        self._base_interval = interval
        self._interval = interval
        self._last_call = 0.0

    def wait(self):
        elapsed = monotonic() - self._last_call

        # self.logging(
        #     f"Checking if wait delay is needed. Time elapsed: {elapsed:.3f}s",
        #     "DEBUG",
        # )
        if elapsed < self._interval:
            wait_time = self._interval - elapsed
            # self.logging(
            #     f"Throttling request for {wait_time:.3f}s, Last request received at {self._last_call}"
            # )
            sleep(wait_time)
        self._last_call = monotonic()

    def set_wait_interval(self, interval: float) -> None:
        self._interval = interval

    def increase_wait_interval(self, amount: float = 0.5) -> None:
        self._interval += amount

        # self.logging(
        #     f"Throttle interval increased to {self._interval:.3f}s",
        #     "WARNING",
        # )

    def delay(self, amount: float) -> None:
        # self.logging(
        #     f"Server requested retry delay of {amount:.3f}s. Waiting...",
        #     "WARNING",
        # )

        sleep(amount)

    def reset_wait_interval(self) -> None:
        self._interval = self._base_interval
