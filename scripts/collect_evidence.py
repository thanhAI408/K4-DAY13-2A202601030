from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "submission" / "evidence"
LOG_PATH = ROOT / "data" / "logs.jsonl"


def run_and_save(command: list[str], destination: Path) -> int:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace")
    destination.write_text(result.stdout + result.stderr, encoding="utf-8")
    print(f"[{result.returncode}] {' '.join(command)} -> {destination.relative_to(ROOT)}")
    return result.returncode


def load_logs() -> list[dict]:
    if not LOG_PATH.exists():
        return []
    rows: list[dict] = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return rows


def export_log_evidence(records: list[dict]) -> None:
    api = [r for r in records if r.get("service") == "api" and r.get("correlation_id")]
    if api:
        cid = api[-1]["correlation_id"]
        related = [r for r in records if r.get("correlation_id") == cid]
        (EVIDENCE / "07-log-correlation.json").write_text(
            json.dumps(related, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
        )
        print(f"Exported correlation evidence: {cid}")

    redacted = [r for r in records if "[REDACTED_" in json.dumps(r, ensure_ascii=False)]
    if redacted:
        (EVIDENCE / "08-pii-redaction.json").write_text(
            json.dumps(redacted[-5:], ensure_ascii=False, indent=2, default=str), encoding="utf-8"
        )
        print("Exported PII redaction evidence")
    else:
        print("No redacted PII record found yet. Send one test request containing email/phone/card first.")


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    run_and_save([sys.executable, "scripts/validate_logs.py"], EVIDENCE / "02-validate-logs.txt")
    run_and_save([sys.executable, "scripts/validate_dashboard.py"], EVIDENCE / "09-validate-dashboard.txt")
    run_and_save([sys.executable, "scripts/build_dashboard.py"], EVIDENCE / "10-dashboard-build.txt")
    export_log_evidence(load_logs())
    print("\nText/JSON evidence collected. Screenshots and Langfuse trace IDs must still be captured from the real run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
