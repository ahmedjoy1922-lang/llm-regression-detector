import hashlib
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_id: str
    api_version: str
    thinking_level: Literal["minimal"]
    max_output_tokens: int = Field(gt=0)
    requests_per_minute: int = Field(gt=0)
    retry_attempts: int = Field(ge=1, le=10)
    max_retry_wait_seconds: int = Field(ge=1, le=300)
    schema_version: str
    cache_path: Path
    dataset_path: Path
    baseline_path: Path
    report_path: Path


def load_settings(path: Path = Path("config.yaml")) -> Settings:
    # Reject unknown or invalid runtime settings at startup.
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return Settings.model_validate(data)


def file_hash(path: Path) -> str:
    # Fingerprint exact bytes so every behavior change is traceable.
    return hashlib.sha256(path.read_bytes()).hexdigest()