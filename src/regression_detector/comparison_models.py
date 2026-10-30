from enum import StrEnum

from pydantic import BaseModel, Field


# Use stable severity values in the CLI and CI exit policy.
class Severity(StrEnum):
    PASS = "PASS"
    WARN = "WARN"
    CRITICAL = "CRITICAL"


# Describe one changed case between compatible runs.
class CaseDelta(BaseModel):
    case_id: str
    before_label: str
    after_label: str
    was_correct: bool
    is_correct: bool


# Summarize the metrics and changed cases used by the gate.
class ComparisonSummary(BaseModel):
    baseline_run_id: str
    candidate_run_id: str
    accuracy_before: float = Field(ge=0, le=1)
    accuracy_after: float = Field(ge=0, le=1)
    accuracy_delta: float
    regressions: list[CaseDelta]
    improvements: list[CaseDelta]
    changed: list[CaseDelta]


# Return both a machine decision and a human-readable reason.
class GateDecision(BaseModel):
    severity: Severity
    exit_code: int = Field(ge=0, le=2)
    reasons: list[str]