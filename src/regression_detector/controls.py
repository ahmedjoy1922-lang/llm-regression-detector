import time
from collections.abc import Callable

RETRYABLE_SERVER_CODES = {500, 502, 503, 504}
PERMANENT_CLIENT_CODES = {400, 401, 403, 404, 422}


class RetryBudgetExceeded(RuntimeError):
    pass


def should_retry(status_code: int, retry_after: float | None) -> bool:
    # Retry servers and explicitly paced quota responses only.
    if status_code in RETRYABLE_SERVER_CODES:
        return True
    return status_code == 429 and retry_after is not None


def retry_delay(
    attempt: int, retry_after: float | None, max_wait: float
) -> float:
    # Honor a server delay when it fits the configured wait budget.
    delay = retry_after if retry_after is not None else 2.0 ** max(0, attempt - 1)
    if delay < 0:
        raise ValueError("retry delay cannot be negative")
    if delay > max_wait:
        raise RetryBudgetExceeded(
            f"required retry delay {delay}s exceeds {max_wait}s"
        )
    return delay


class RequestPacer:
    def __init__(
        self,
        requests_per_minute: int,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        if requests_per_minute <= 0:
            raise ValueError("requests_per_minute must be positive")
        self.interval = 60.0 / requests_per_minute
        self.clock = clock
        self.sleeper = sleeper
        self.last_request: float | None = None

    def wait(self) -> None:
        now = self.clock()
        if self.last_request is not None:
            remaining = self.interval - (now - self.last_request)
            if remaining > 0:
                self.sleeper(remaining)
        self.last_request = self.clock()