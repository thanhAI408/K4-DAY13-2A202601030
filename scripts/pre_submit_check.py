from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> bool:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace")
    print(f"\n$ {' '.join(command)}")
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="")
    return result.returncode == 0


def main() -> int:
    ok = True
    ok &= run([sys.executable, "-m", "pytest", "-q"])
    ok &= run([sys.executable, "scripts/validate_logs.py"])
    ok &= run([sys.executable, "scripts/validate_dashboard.py"])

    challenge_ok = run(["git", "diff", "--exit-code", "--", "config/challenge.json"])
    if not challenge_ok:
        print("FAIL: config/challenge.json đã bị sửa. Khôi phục file chính thức trước khi nộp.")
    ok &= challenge_ok

    tracked_env = subprocess.run(
        ["git", "ls-files", "--error-unmatch", ".env"], cwd=ROOT, capture_output=True
    ).returncode == 0
    if tracked_env:
        print("FAIL: .env đang bị track bởi Git.")
        ok = False
    else:
        print("PASS: .env không bị track.")

    report = (ROOT / "submission" / "REPORT.md").read_text(encoding="utf-8")
    markers = ["CHƯA THU THẬP RUNTIME", "CHƯA CÓ COMMIT/PR THẬT", "[ĐIỀN SAU KHI CHẠY]", "[DÁN LINK COMMIT/PR]"]
    remaining = [marker for marker in markers if marker in report]
    if remaining:
        print(f"WARN: REPORT.md còn placeholder: {', '.join(remaining)}")
        ok = False

    print("\nREADY TO SUBMIT" if ok else "\nNOT READY - xử lý các mục FAIL/WARN phía trên")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
