from types import SimpleNamespace as NS

import pytest
from google.genai import errors

from regression_detector.api import _retry_after, _usage, request_prediction
from regression_detector.config import load_settings
from regression_detector.controls import RequestPacer
from regression_detector.prompts import PromptSpec


def test_retry_info_delay_is_extracted() -> None:
    exc = errors.ClientError(429, {
        "error": {"details": [{"retryDelay": "12s"}]}
    })
    assert _retry_after(exc) == 12


def test_missing_total_usage_fails_closed() -> None:
    response = NS(usage_metadata=NS(
        prompt_token_count=2, candidates_token_count=1,
        thoughts_token_count=0, total_token_count=None,
    ))
    with pytest.raises(RuntimeError, match="total token"):
        _usage(response)


def test_malformed_prediction_is_not_accepted() -> None:
    response = NS(candidates=[NS(finish_reason=NS(value="STOP"))], text="not json")
    client = NS(models=NS(generate_content=lambda **_: response))
    pacer = RequestPacer(60, clock=lambda: 0.0, sleeper=lambda _: None)
    spec = PromptSpec(version="v1", system="Classify.", user_template="{{ ticket_text }}")
    with pytest.raises(ValueError):
        request_prediction(client, load_settings(), spec, "fictional ticket", pacer)