from pathlib import Path

import typer

from .compare import compare_runs, load_run
from .gate import evaluate_gate, load_policy

app = typer.Typer(add_completion=False)


# Print the decision, preserve its evidence, and return its exit code.
@app.command()
def main(
    baseline_path: Path = Path("runs/baseline.json"),
    candidate_path: Path = Path("runs/degraded.json"),
    output_path: Path = Path("reports/gate.json"),
) -> None:
    baseline = load_run(baseline_path)
    candidate = load_run(candidate_path)
    summary = compare_runs(baseline, candidate)
    decision = evaluate_gate(summary, baseline, candidate, load_policy())
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(decision.model_dump_json(indent=2), encoding="utf-8")
    typer.echo(decision.severity.value)
    for reason in decision.reasons:
        typer.echo(f"- {reason}")
    raise typer.Exit(code=decision.exit_code)


if __name__ == "__main__":
    app()