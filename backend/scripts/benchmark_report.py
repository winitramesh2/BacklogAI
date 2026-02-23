import argparse
import json
from pathlib import Path


def _read(path: Path) -> dict:
    return json.loads(path.read_text())


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare benchmark outputs and print deltas")
    parser.add_argument("--baseline", required=True, help="Path to baseline benchmark JSON")
    parser.add_argument("--current", required=True, help="Path to current benchmark JSON")
    parser.add_argument("--output", default="backend/eval/benchmark_delta_report.json")
    args = parser.parse_args()

    baseline = _read(Path(args.baseline))
    current = _read(Path(args.current))

    baseline_report = baseline.get("report", baseline)
    current_report = current.get("report", current)

    metrics = [
        "first_pass_syncable_rate",
        "avg_gherkin_ratio",
        "avg_citation_coverage",
        "avg_quality_score",
        "avg_execution_readiness_score",
    ]

    deltas = {}
    for key in metrics:
        base_value = float(baseline_report.get(key, 0.0))
        current_value = float(current_report.get(key, 0.0))
        deltas[key] = {
            "baseline": base_value,
            "current": current_value,
            "delta": round(current_value - base_value, 4),
        }

    result = {
        "baseline": str(args.baseline),
        "current": str(args.current),
        "deltas": deltas,
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
