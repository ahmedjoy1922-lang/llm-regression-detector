from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .comparison_models import ComparisonSummary, GateDecision, Severity
from .run_models import EvaluationRun
from .run_signals import increase_ratio, p95_latency_ms, total_tokens


class GatePolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    warning_accuracy_drop: float = Field(ge=0, le=1)
    critical_accuracy_drop: float = Field(ge=0, le=1)
    critical_regression_count: int = Field(ge=1)
    warning_token_increase: float = Field(ge=0)
    warning_p95_latency_increase: float = Field(ge=0)

    @model_validator(mode="after")
    def validate_order(self) -> "GatePolicy":
        if self.critical_accuracy_drop < self.warning_accuracy_drop:
            raise ValueError("critical accuracy drop must be at least the warning drop")
        return self


def load_policy(path: Path = Path("policy.yaml")) -> GatePolicy:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return GatePolicy.model_validate(data)


def evaluate_gate(
    summary: ComparisonSummary, baseline: EvaluationRun,
    candidate: EvaluationRun, policy: GatePolicy,
) -> GateDecision:
    if summary.baseline_run_id != baseline.run_id:
        raise ValueError("summary baseline_run_id mismatch")
    if summary.candidate_run_id != candidate.run_id:
        raise ValueError("summary candidate_run_id mismatch")
    accuracy_drop = max(0.0, -summary.accuracy_delta)
    token_growth = increase_ratio(total_tokens(baseline), total_tokens(candidate))
    latency_growth = increase_ratio(
        p95_latency_ms(baseline), p95_latency_ms(candidate)
    )
    critical = (
        accuracy_drop >= policy.critical_accuracy_drop
        or len(summary.regressions) >= policy.critical_regression_count
    )
    warning = (
        accuracy_drop >= policy.warning_accuracy_drop
        or token_growth >= policy.warning_token_increase
        or latency_growth >= policy.warning_p95_latency_increase
    )
    reasons = [
        f"accuracy_drop={accuracy_drop:.1%}",
        f"regressions={len(summary.regressions)}",
        f"token_growth={token_growth:.1%}",
        f"p95_latency_growth={latency_growth:.1%}",
    ]
    if critical:
        return GateDecision(severity=Severity.CRITICAL, exit_code=2, reasons=reasons)
    if warning:
        return GateDecision(severity=Severity.WARN, exit_code=1, reasons=reasons)
    return GateDecision(severity=Severity.PASS, exit_code=0, reasons=reasons)