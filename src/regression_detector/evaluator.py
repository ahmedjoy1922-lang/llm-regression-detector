import os
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from .cache import ResponseCache
from .classification import classify_case
from .config import file_hash, load_settings
from .controls import RequestPacer
from .dataset import dataset_hash, load_cases
from .prompts import load_prompt
from .run_models import CaseResult, EvaluationRun, EvaluationSettings


def run_evaluation(prompt_path: Path, output_path: Path) -> EvaluationRun:
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing")
    settings = load_settings()
    cases = load_cases(settings.dataset_path)
    spec = load_prompt(prompt_path)
    prompt_digest = file_hash(prompt_path)
    cache = ResponseCache(settings.cache_path)
    pacer = RequestPacer(settings.requests_per_minute)
    results: list[CaseResult] = []
    http_options = types.HttpOptions(
        api_version=settings.api_version,
        retry_options=types.HttpRetryOptions(attempts=1),
    )
    try:
        with genai.Client(api_key=api_key, http_options=http_options) as client:
            for case in cases:
                prediction, measurement, run_usage, hit = classify_case(
                    client, settings, spec, prompt_digest, case, cache, pacer
                )
                results.append(CaseResult(
                    case_id=case.case_id,
                    expected_label=case.expected_label,
                    prediction=prediction,
                    correct=prediction.label == case.expected_label,
                    api_measurement=measurement,
                    run_api_usage=run_usage,
                    cache_hit=hit,
                ))
    finally:
        cache.close()

    created = datetime.now(UTC)
    run = EvaluationRun(
        run_id=f"{spec.version}-{created:%Y%m%dT%H%M%SZ}",
        created_at=created,
        model_id=settings.model_id,
        prompt_version=spec.version,
        prompt_hash=prompt_digest,
        dataset_hash=dataset_hash(cases),
        settings=EvaluationSettings(
            api_version=settings.api_version,
            sdk_version=version("google-genai"),
            thinking_level=settings.thinking_level,
            max_output_tokens=settings.max_output_tokens,
            schema_version=settings.schema_version,
        ),
        results=results,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(run.model_dump_json(indent=2), encoding="utf-8")
    return run