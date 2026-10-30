from pathlib import Path

from regression_detector.config import file_hash, load_settings


def test_load_settings() -> None:
    # Confirm every reproducibility control reaches the typed loader.
    settings = load_settings()
    assert settings.model_id == "gemini-3.5-flash-lite"
    assert settings.api_version == "v1beta"
    assert settings.thinking_level == "minimal"
    assert settings.schema_version == "prediction-v2"
    assert settings.max_retry_wait_seconds == 60
    assert not hasattr(settings, "temperature")


def test_prompt_hashes_differ() -> None:
    # A version-only prompt change must still produce a new fingerprint.
    first = file_hash(Path("prompts/classifier-v1.yaml"))
    second = file_hash(Path("prompts/classifier-v2.yaml"))
    assert len(first) == 64
    assert first != second