from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .domain import Label, Prediction


class UsageStats(BaseModel):
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    thought_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)

    @classmethod
    def zero(cls) -> "UsageStats":
        return cls(input_tokens=0, output_tokens=0, thought_tokens=0, total_tokens=0)

    @model_validator(mode="after")
    def totals_are_consistent(self) -> "UsageStats":
        subtotal = self.input_tokens + self.output_tokens + self.thought_tokens
        if self.total_tokens < subtotal:
            raise ValueError("total_tokens is smaller than its components")
        return self


class ApiMeasurement(BaseModel):
    latency_ms: float = Field(gt=0)
    usage: UsageStats


class EvaluationSettings(BaseModel):
    api_version: str
    sdk_version: str
    thinking_level: Literal["minimal"]
    max_output_tokens: int = Field(gt=0)
    schema_version: str


class CaseResult(BaseModel):
    case_id: str = Field(pattern=r"^case-[0-9]{3}$")
    expected_label: Label
    prediction: Prediction
    correct: bool
    api_measurement: ApiMeasurement
    run_api_usage: UsageStats
    cache_hit: bool

    @model_validator(mode="after")
    def evidence_is_consistent(self) -> "CaseResult":
        if self.correct != (self.prediction.label == self.expected_label):
            raise ValueError("correct disagrees with the labels")
        expected = UsageStats.zero() if self.cache_hit else self.api_measurement.usage
        if self.run_api_usage != expected:
            raise ValueError("run_api_usage disagrees with cache provenance")
        return self


class EvaluationRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    created_at: datetime
    model_id: str
    prompt_version: str
    prompt_hash: str
    dataset_hash: str
    settings: EvaluationSettings
    results: list[CaseResult] = Field(min_length=1)

    @model_validator(mode="after")
    def case_ids_are_unique(self) -> "EvaluationRun":
        case_ids = [result.case_id for result in self.results]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("evaluation run contains duplicate case IDs")
        return self