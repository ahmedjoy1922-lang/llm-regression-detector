from collections import defaultdict

from .domain import TicketCase
from .run_models import EvaluationRun


# Calculate correct and total counts for each human-defined slice.
def slice_scores(
    run: EvaluationRun, cases: list[TicketCase]
) -> dict[str, tuple[int, int]]:
    slice_by_id = {case.case_id: case.slice for case in cases}
    totals: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for result in run.results:
        name = slice_by_id[result.case_id]
        totals[name][1] += 1
        totals[name][0] += int(result.correct)
    return {name: (values[0], values[1]) for name, values in totals.items()}


# Format changed cases for terminal and CI logs.
def regression_rows(run: EvaluationRun, case_ids: set[str]) -> list[str]:
    rows: list[str] = []
    for result in run.results:
        if result.case_id in case_ids:
            rows.append(
                f"{result.case_id}: {result.expected_label} -> "
                f"{result.prediction.label.value}"
            )
    return rows