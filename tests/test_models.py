from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from regression_detector.domain import Prediction, TicketCase
from regression_detector.run_models import EvaluationRun


def test_valid_prediction() -> None:
    prediction = Prediction(
        label="technical", confidence=0.9, rationale="Device fails"
    )
    assert prediction.label == "technical"


def test_unknown_expected_label_is_rejected() -> None:
    with pytest.raises(ValidationError):
        TicketCase.model_validate({
            "case_id": "case-001",
            "text": "Please change the delivery address",
            "expected_label": "shipping",
            "slice": "clear",
        })


def test_empty_evaluation_run_is_rejected() -> None:
    with pytest.raises(ValidationError):
        EvaluationRun(
            run_id="empty", created_at=datetime.now(UTC), model_id="model",
            prompt_version="v1", prompt_hash="a", dataset_hash="b",
            settings={"api_version": "v1beta", "sdk_version": "2.33.0",
                      "thinking_level": "minimal", "max_output_tokens": 200,
                      "schema_version": "prediction-v2"},
            results=[],
        )