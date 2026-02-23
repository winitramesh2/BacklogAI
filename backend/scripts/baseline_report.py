import argparse
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _gherkin_ratio(criteria: list[str]) -> float:
    if not criteria:
        return 0.0
    valid = [c for c in criteria if "given" in c.lower() and "when" in c.lower() and "then" in c.lower()]
    return len(valid) / len(criteria)


def _build_report(scenarios: list[dict]) -> dict:
    client = TestClient(app)
    rows: list[dict] = []

    for index, scenario in enumerate(scenarios, start=1):
        resp = client.post("/backlog/generate/v2", json=scenario)
        if resp.status_code != 200:
            rows.append({
                "index": index,
                "status": resp.status_code,
                "error": resp.text,
            })
            continue

        payload = resp.json()
        warning_details = payload.get("warning_details", [])
        high_warnings = [w for w in warning_details if str(w.get("severity", "")).lower() == "high"]
        quality_score = float(payload.get("quality_score", 0.0))
        execution_score = float(payload.get("execution_readiness_score", 0.0))
        gherkin_ratio = _gherkin_ratio(payload.get("acceptance_criteria", []))
        citation_coverage = float(
            (payload.get("research_summary") or {}).get("quality", {}).get("citation_coverage", 0.0)
        )

        rows.append(
            {
                "index": index,
                "status": 200,
                "quality_score": quality_score,
                "execution_readiness_score": execution_score,
                "gherkin_ratio": gherkin_ratio,
                "citation_coverage": citation_coverage,
                "high_warning_count": len(high_warnings),
                "syncable_first_pass": quality_score >= 70.0 and execution_score >= 70.0 and len(high_warnings) == 0,
            }
        )

    successful = [row for row in rows if row.get("status") == 200]
    total = len(rows)
    success_count = len(successful)

    def _avg(key: str) -> float:
        if not successful:
            return 0.0
        return round(sum(float(row.get(key, 0.0)) for row in successful) / len(successful), 3)

    report = {
        "total_scenarios": total,
        "successful_runs": success_count,
        "success_rate": round(success_count / total, 3) if total else 0.0,
        "first_pass_syncable_rate": round(
            sum(1 for row in successful if row.get("syncable_first_pass")) / success_count, 3
        ) if success_count else 0.0,
        "avg_quality_score": _avg("quality_score"),
        "avg_execution_readiness_score": _avg("execution_readiness_score"),
        "avg_gherkin_ratio": _avg("gherkin_ratio"),
        "avg_citation_coverage": _avg("citation_coverage"),
        "rows": rows,
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate baseline quality report for BacklogAI v2 story preview")
    parser.add_argument("--scenarios", default="backend/eval/golden_scenarios.jsonl")
    parser.add_argument("--output", default="backend/eval/latest_baseline_report.json")
    args = parser.parse_args()

    scenarios = _read_jsonl(Path(args.scenarios))
    report = _build_report(scenarios)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
