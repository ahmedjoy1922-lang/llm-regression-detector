import time
from typing import Any

from google import genai
from google.genai import errors, types

from .config import Settings
from .controls import RequestPacer, retry_delay, should_retry
from .domain import Prediction
from .prompts import PromptSpec, render_ticket
from .run_models import ApiMeasurement, UsageStats


def _seconds(value: object) -> float | None:
    if not isinstance(value, str):
        return None
    text = value.strip().removesuffix("s")
    try:
        return float(text)
    except ValueError:
        return None


def _retry_after(exc: errors.APIError) -> float | None:
    # Prefer HTTP metadata, then Google's RetryInfo payload.
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", {}) if response else {}
    header_delay = _seconds(headers.get("Retry-After"))
    if header_delay is not None:
        return header_delay
    details: Any = getattr(exc, "details", {})
    error = details.get("error", details) if isinstance(details, dict) else {}
    for item in error.get("details", []):
        if isinstance(item, dict) and "retryDelay" in item:
            return _seconds(item["retryDelay"])
    return None


def _usage(response: object) -> UsageStats:
    metadata = getattr(response, "usage_metadata", None)
    if metadata is None:
        raise RuntimeError("Gemini omitted usage metadata")
    values = {
        "input_tokens": getattr(metadata, "prompt_token_count", None),
        "output_tokens": getattr(metadata, "candidates_token_count", None),
        "thought_tokens": getattr(metadata, "thoughts_token_count", 0) or 0,
        "total_tokens": getattr(metadata, "total_token_count", None),
    }
    if values["input_tokens"] is None or values["output_tokens"] is None:
        raise RuntimeError("Gemini returned incomplete usage metadata")
    if values["total_tokens"] is None:
        raise RuntimeError("Gemini omitted total token usage")
    return UsageStats.model_validate(values)


def request_prediction(
    client: genai.Client, settings: Settings, spec: PromptSpec,
    ticket_text: str, pacer: RequestPacer,
) -> tuple[Prediction, ApiMeasurement]:
    for attempt in range(1, settings.retry_attempts + 1):
        pacer.wait()
        started = time.perf_counter()
        try:
            response = client.models.generate_content(
                model=settings.model_id,
                contents=render_ticket(spec, ticket_text),
                config=types.GenerateContentConfig(
                    system_instruction=spec.system,
                    thinking_config=types.ThinkingConfig(
                        thinking_level=settings.thinking_level
                    ),
                    max_output_tokens=settings.max_output_tokens,
                    response_mime_type="application/json",
                    response_json_schema=Prediction.model_json_schema(),
                ),
            )
            candidates = response.candidates or []
            if not candidates:
                raise RuntimeError("Gemini returned no candidates")
            reason = getattr(candidates[0], "finish_reason", None)
            if getattr(reason, "value", reason) != "STOP":
                raise RuntimeError(f"Gemini stopped with finish reason {reason}")
            prediction = Prediction.model_validate_json(response.text or "")
            measurement = ApiMeasurement(
                latency_ms=(time.perf_counter() - started) * 1000,
                usage=_usage(response),
            )
            return prediction, measurement
        except errors.APIError as exc:
            delay = _retry_after(exc)
            if attempt == settings.retry_attempts or not should_retry(exc.code, delay):
                raise
            time.sleep(retry_delay(attempt, delay, settings.max_retry_wait_seconds))
    raise RuntimeError("retry loop ended unexpectedly")