
from pathlib import Path
from regression_detector.compare import compare_runs, load_run

# Load baseline and mutated candidate runs
baseline = load_run(Path("runs/baseline.json"))
degraded = load_run(Path("runs/degraded.json"))

# Run the comparison engine
comparison = compare_runs(baseline, degraded)

# Save the detailed typed comparison report
Path("runs/degraded-comparison.json").write_text(comparison.model_dump_json(indent=2))

# Print out the results summary
print(f"delta={comparison.accuracy_delta:+.1%} changed={len(comparison.changed)} regressions={len(comparison.regressions)}")
