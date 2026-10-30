from importlib.metadata import version

from google import genai
from pydantic import BaseModel

from .api import request_prediction
from .cache import ResponseCache, make_cache_key
from .config import Settings
from .controls import RequestPacer
from .domain import Prediction, TicketCase
from .prompts import PromptSpec
from .run_models import ApiMeasurement, UsageStats


class CachedResponse(BaseModel):
    prediction: Prediction
    api_measurement: ApiMeasurement


def classify_case(
    client: genai.Client, settings: Settings, spec: PromptSpec,
    prompt_hash: str, case: TicketCase, cache: ResponseCache,
    pacer: RequestPacer,
) -> tuple[Prediction, ApiMeasurement, UsageStats, bool]:
    sdk_version = version("google-genai")
    key = make_cache_key(
        model_id=settings.model_id,
        prompt_hash=prompt_hash,
        ticket_text=case.text,
        api_version=settings.api_version,
        thinking_level=settings.thinking_level,
        max_output_tokens=settings.max_output_tokens,
        schema_version=settings.schema_version,
        sdk_version=sdk_version,
    )
    cached_json = cache.get(key)
    if cached_json is not None:
        cached = CachedResponse.model_validate_json(cached_json)
        return (
            cached.prediction,
            cached.api_measurement,
            UsageStats.zero(),
            True,
        )

    prediction, measurement = request_prediction(
        client, settings, spec, case.text, pacer
    )
    cached = CachedResponse(
        prediction=prediction,
        api_measurement=measurement,
    )
    cache.put(key, cached.model_dump_json())
    return prediction, measurement, measurement.usage, False