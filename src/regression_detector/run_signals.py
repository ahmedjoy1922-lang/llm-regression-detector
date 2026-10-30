import math

from .run_models import EvaluationRun


def total_tokens(run: EvaluationRun) -> int:
    # Compare original API measurements, including cache hits.
    total = sum(
        result.api_measurement.usage.total_tokens
        for result in run.results
    )
    if total <= 0:
        raise ValueError("run has no original token measurements")
    return total


def p95_latency_ms(run: EvaluationRun) -> float:
    # Use original live latencies so warm-cache speed cannot hide a slowdown.
    values = sorted(
        result.api_measurement.latency_ms
        for result in run.results
    )
    if not values:
        raise ValueError("run has no latency measurements")
    index = math.ceil(0.95 * len(values)) - 1
    return values[index]


def increase_ratio(before: float, after: float) -> float:
    if before <= 0:
        raise ValueError("baseline signal must be positive")
    if after < 0:
        raise ValueError("candidate signal cannot be negative")
    return (after - before) / before