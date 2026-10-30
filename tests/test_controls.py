from pathlib import Path

import pytest

from regression_detector.cache import ResponseCache, make_cache_key
from regression_detector.controls import (
    RETRYABLE_SERVER_CODES, RequestPacer, RetryBudgetExceeded,
    retry_delay, should_retry,
)


def key(**changes: object) -> str:
    values = {
        "model_id": "model", "prompt_hash": "prompt", "ticket_text": "ticket",
        "api_version": "v1beta", "thinking_level": "minimal",
        "max_output_tokens": 120, "schema_version": "prediction-v2",
        "sdk_version": "2.33.0",
    }
    values.update(changes)
    return make_cache_key(**values)


def test_cache_round_trip(tmp_path: Path) -> None:
    cache = ResponseCache(tmp_path / "responses.sqlite3")
    cache.put("abc", '{"prediction":{"label":"billing"},"api_measurement":{}}')
    assert cache.get("abc") is not None
    assert cache.get("missing") is None
    cache.close()


@pytest.mark.parametrize("field,value", [
    ("api_version", "v1"), ("thinking_level", "low"),
    ("max_output_tokens", 121), ("schema_version", "prediction-v3"),
    ("sdk_version", "2.34.0"),
])
def test_every_behavior_setting_changes_the_key(field: str, value: object) -> None:
    assert key() != key(**{field: value})


def test_retry_policy_respects_server_delay_and_budget() -> None:
    assert RETRYABLE_SERVER_CODES == {500, 502, 503, 504}
    assert should_retry(503, None)
    assert should_retry(429, 12)
    assert not should_retry(429, None)
    assert not should_retry(401, None)
    assert retry_delay(2, 12, 60) == 12
    with pytest.raises(RetryBudgetExceeded):
        retry_delay(2, 120, 60)


def test_pacer_uses_fake_time_without_real_sleep() -> None:
    now = [0.0]
    simulated_waits: list[float] = []

    def fake_sleep(seconds: float) -> None:
        simulated_waits.append(seconds)
        now[0] += seconds

    pacer = RequestPacer(60, clock=lambda: now[0], sleeper=fake_sleep)
    pacer.wait()
    now[0] = 0.25
    pacer.wait()

    assert simulated_waits == [pytest.approx(0.75)]
    assert now[0] == pytest.approx(1.0)
    assert pacer.last_request == pytest.approx(1.0)