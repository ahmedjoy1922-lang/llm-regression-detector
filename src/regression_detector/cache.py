import hashlib
import json
import sqlite3
from pathlib import Path


def make_cache_key(
    *, model_id: str, prompt_hash: str, ticket_text: str,
    api_version: str, thinking_level: str, max_output_tokens: int,
    schema_version: str, sdk_version: str,
) -> str:
    # Include every input that can change the validated response.
    payload = {
        "api_version": api_version,
        "max_output_tokens": max_output_tokens,
        "model_id": model_id,
        "prompt_hash": prompt_hash,
        "schema_version": schema_version,
        "sdk_version": sdk_version,
        "thinking_level": thinking_level,
        "ticket_text": ticket_text,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ResponseCache:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS responses "
            "(cache_key TEXT PRIMARY KEY, response_json TEXT NOT NULL)"
        )

    def get(self, cache_key: str) -> str | None:
        row = self.connection.execute(
            "SELECT response_json FROM responses WHERE cache_key = ?", (cache_key,)
        ).fetchone()
        return row[0] if row else None

    def put(self, cache_key: str, response_json: str) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO responses VALUES (?, ?)",
            (cache_key, response_json),
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()