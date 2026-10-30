import hashlib
import json
from collections import Counter
from pathlib import Path

from pydantic import TypeAdapter

from .domain import TicketCase

CASE_LIST = TypeAdapter(list[TicketCase])


def load_cases(path: Path) -> list[TicketCase]:
    # Validate the complete file before an evaluator can use it.
    raw = json.loads(path.read_text(encoding="utf-8"))
    cases = CASE_LIST.validate_python(raw)
    if not cases:
        raise ValueError("golden dataset must contain at least one case")
    ids = [case.case_id for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("case_id values must be unique")
    return cases


def dataset_hash(cases: list[TicketCase]) -> str:
    # Reject meaningless fingerprints for empty in-memory datasets.
    if not cases:
        raise ValueError("cannot hash an empty dataset")
    payload = [case.model_dump(mode="json") for case in cases]
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def label_counts(cases: list[TicketCase]) -> Counter[str]:
    # Expose label balance as an observable dataset check.
    return Counter(case.expected_label.value for case in cases)