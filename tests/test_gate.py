from datetime import UTC, datetime

from regression_detector.compare import compare_runs
from regression_detector.domain import Label, Prediction
from regression_detector.gate import GatePolicy, evaluate_gate
from regression_detector.run_models import (
    ApiMeasurement, CaseResult, EvaluationRun, EvaluationSettings, UsageStats,
)


def make_run(run_id: str, label: Label, tokens: int, latency: float) -> EvaluationRun:
    usage = UsageStats(
        input_tokens=tokens - 1,
        output_tokens=1,
        thought_tokens=0,
        total_tokens=tokens,
    )
    return EvaluationRun(
        run_id=run_id,
        created_at=datetime.now(UTC),
        model_id="model",
        prompt_version=run_id,
        prompt_hash=run_id,
        dataset_hash="dataset",
        settings=EvaluationSettings(
            api_version="v1beta",
            sdk_version="2.33.0",
            thinking_level="minimal",
            max_output_tokens=120,
            schema_version="prediction-v2",
        ),
        results=[CaseResult(
            case_id="case-001",
            expected_label=Label.BILLING,
            prediction=Prediction(label=label, confidence=0.9, rationale="test"),
            correct=label == Label.BILLING,
            api_measurement=ApiMeasurement(latency_ms=latency, usage=usage),
            run_api_usage=usage,
            cache_hit=False,
        )],
    )


def policy() -> GatePolicy:
    return GatePolicy(
        warning_accuracy_drop=0.01,
        critical_accuracy_drop=0.5,
        critical_regression_count=1,
        warning_token_increase=0.25,
        warning_p95_latency_increase=0.5,
    )


def decision(baseline: EvaluationRun, candidate: EvaluationRun):
    return evaluate_gate(compare_runs(baseline, candidate), baseline, candidate, policy())


def test_pass_warn_and_critical_paths() -> None:
    baseline = make_run("base", Label.BILLING, 10, 100)
    assert decision(baseline, make_run("pass", Label.BILLING, 10, 100)).exit_code == 0
    assert decision(baseline, make_run("warn", Label.BILLING, 13, 100)).exit_code == 1
    assert decision(baseline, make_run("critical", Label.TECHNICAL, 10, 100)).exit_code == 2


def test_cached_run_uses_original_measurement() -> None:
    baseline = make_run("base", Label.BILLING, 10, 100)
    candidate = make_run("cached", Label.BILLING, 13, 100)
    candidate.results[0].cache_hit = True
    candidate.results[0].run_api_usage = UsageStats.zero()

    assert candidate.results[0].api_measurement.usage.total_tokens == 13
    assert candidate.results[0].run_api_usage == UsageStats.zero()
    assert decision(baseline, candidate).exit_code == 1