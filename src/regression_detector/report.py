from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .compare import compare_runs, load_run
from .gate import evaluate_gate, load_policy


# Render typed comparison evidence into a portable HTML report.
def render_report(
    baseline_path: Path,
    candidate_path: Path,
    output_path: Path,
) -> Path:
    baseline = load_run(baseline_path)
    candidate = load_run(candidate_path)
    summary = compare_runs(baseline, candidate)
    decision = evaluate_gate(summary, baseline, candidate, load_policy())
    environment = Environment(
        loader=FileSystemLoader("templates"),
        autoescape=select_autoescape(["html"]),
    )
    html = environment.get_template("report.html").render(
        summary=summary,
        decision=decision,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path