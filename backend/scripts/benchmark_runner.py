import argparse
import json
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from baseline_report import _build_report, _read_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(description="Run benchmark and enforce quality thresholds")
    parser.add_argument("--scenarios", default="backend/eval/golden_scenarios.jsonl")
    parser.add_argument("--output", default="backend/eval/latest_benchmark_report.json")
    parser.add_argument("--min-syncable", type=float, default=0.70)
    parser.add_argument("--min-gherkin", type=float, default=0.90)
    parser.add_argument("--min-citation", type=float, default=0.85)
    parser.add_argument("--min-quality", type=float, default=75.0)
    parser.add_argument("--min-execution", type=float, default=75.0)
    args = parser.parse_args()

    scenarios = _read_jsonl(Path(args.scenarios))
    report = _build_report(scenarios)

    checks = {
        "first_pass_syncable_rate": report.get("first_pass_syncable_rate", 0.0) >= args.min_syncable,
        "avg_gherkin_ratio": report.get("avg_gherkin_ratio", 0.0) >= args.min_gherkin,
        "avg_citation_coverage": report.get("avg_citation_coverage", 0.0) >= args.min_citation,
        "avg_quality_score": report.get("avg_quality_score", 0.0) >= args.min_quality,
        "avg_execution_readiness_score": report.get("avg_execution_readiness_score", 0.0) >= args.min_execution,
    }

    result = {
        "thresholds": {
            "min_syncable": args.min_syncable,
            "min_gherkin": args.min_gherkin,
            "min_citation": args.min_citation,
            "min_quality": args.min_quality,
            "min_execution": args.min_execution,
        },
        "checks": checks,
        "report": report,
        "passed": all(checks.values()),
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))

    if not result["passed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
