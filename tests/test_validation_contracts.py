import pytest
from pydantic import ValidationError

from regression_detector.classification import CachedResponse
from regression_detector.config import Settings, load_settings
from regression_detector.domain import Prediction


def test_unknown_config_key_is_rejected() -> None:
    data = load_settings().model_dump()
    data["temperature"] = 0
    with pytest.raises(ValidationError, match="temperature"):
        Settings.model_validate(data)


def test_stale_cache_payload_is_rejected() -> None:
    stale = {
        "prediction": {
            "label": "billing", "confidence": 0.9, "rationale": "test"
        }
    }
    with pytest.raises(ValidationError, match="api_measurement"):
        CachedResponse.model_validate(stale)


def test_invalid_prediction_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Prediction(label="billing", confidence=1.5, rationale="Outside range")