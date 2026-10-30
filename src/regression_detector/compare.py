from pathlib import Path

from .comparison_models import CaseDelta, ComparisonSummary
from .run_models import EvaluationRun


def load_run(path: Path) -> EvaluationRun:
    # Revalidate saved evidence before comparison.
    return EvaluationRun.model_validate_json(path.read_text(encoding="utf-8"))


def compare_runs(
    baseline: EvaluationRun, candidate: EvaluationRun
) -> ComparisonSummary:
    # Refuse comparisons where any execution control changed.
    compatibility = {
        "model_id": (baseline.model_id, candidate.model_id),
        "dataset_hash": (baseline.dataset_hash, candidate.dataset_hash),
        "settings": (baseline.settings, candidate.settings),
    }
    mismatches = [name for name, pair in compatibility.items() if pair[0] != pair[1]]
    if mismatches:
        raise ValueError("mismatch: incompatible runs: " + ", ".join(mismatches))

    before = {result.case_id: result for result in baseline.results}
    after = {result.case_id: result for result in candidate.results}
    if before.keys() != after.keys():
        raise ValueError("case_id set mismatch")
    changed: list[CaseDelta] = []
    for case_id, old in before.items():
        new = after[case_id]
        if old.prediction.label != new.prediction.label:
            changed.append(CaseDelta(
                case_id=case_id,
                before_label=old.prediction.label.value,
                after_label=new.prediction.label.value,
                was_correct=old.correct,
                is_correct=new.correct,
            ))
    regressions = [item for item in changed if item.was_correct and not item.is_correct]
    improvements = [item for item in changed if not item.was_correct and item.is_correct]
    before_accuracy = sum(item.correct for item in baseline.results) / len(before)
    after_accuracy = sum(item.correct for item in candidate.results) / len(after)
    return ComparisonSummary(
        baseline_run_id=baseline.run_id,
        candidate_run_id=candidate.run_id,
        accuracy_before=before_accuracy,
        accuracy_after=after_accuracy,
        accuracy_delta=after_accuracy - before_accuracy,
        regressions=regressions,
        improvements=improvements,
        changed=changed,
    )