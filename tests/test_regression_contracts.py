from pathlib import Path

import pytest
from pydantic import ValidationError

from regression_detector.compare import compare_runs, load_run
from regression_detector.gate import evaluate_gate, load_policy


def runs():
    return (
        load_run(Path("tests/fixtures/baseline.json")),
        load_run(Path("tests/fixtures/candidate.json")),
    )


def test_approved_fixture_passes() -> None:
    baseline, candidate = runs()
    summary = compare_runs(baseline, candidate)
    assert evaluate_gate(summary, baseline, candidate, load_policy()).exit_code == 0


@pytest.mark.parametrize("field", ["dataset_hash", "settings"])
def test_incompatible_runs_are_rejected(field: str) -> None:
    baseline, candidate = runs()
    value = "different" if field == "dataset_hash" else candidate.settings.model_copy(update={"schema_version": "v3"})
    candidate = candidate.model_copy(update={field: value})
    with pytest.raises(ValueError, match="mismatch"):
        compare_runs(baseline, candidate)


def test_duplicate_case_ids_are_rejected() -> None:
    _, candidate = runs()
    data = candidate.model_dump()
    data["results"].append(data["results"][0])
    with pytest.raises(ValidationError, match="duplicate"):
        candidate.__class__.model_validate(data)