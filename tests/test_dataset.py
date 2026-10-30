from pathlib import Path

import pytest

from regression_detector.dataset import dataset_hash, label_counts, load_cases


def test_golden_dataset() -> None:
    # Prove the checked-in set is balanced and identifiable.
    cases = load_cases(Path("data/golden.json"))
    assert len(cases) == 18
    assert label_counts(cases) == {
        "billing": 6,
        "technical": 6,
        "account": 6,
    }
    assert len(dataset_hash(cases)) == 64


def test_empty_dataset_file_is_rejected(tmp_path: Path) -> None:
    # Prevent an empty file from producing meaningless perfect metrics.
    path = tmp_path / "empty.json"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="at least one case"):
        load_cases(path)


def test_empty_in_memory_dataset_is_rejected() -> None:
    with pytest.raises(ValueError, match="empty dataset"):
        dataset_hash([])