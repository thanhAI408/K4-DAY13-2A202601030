from __future__ import annotations

import argparse
import html
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean


def parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def percentile(values: list[int], p: int) -> float:
    if not values:
        return 0.0
    items = sorted(values)
    idx = max(0, min(len(items) - 1, round((p / 100) * len(items) + 0.5) - 1))
    return float(items[idx])


def load_window(log_path: Path, minutes: int) -> list[dict]:
    if not log_path.exists():
        return []
    records: list[dict] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = parse_ts(record.get("ts"))
        if ts:
            record["_ts"] = ts
            records.append(record)
    if not records:
        return []
    end = max(record["_ts"] for record in records)
    start = end - timedelta(minutes=minutes)
    return [record for record in records if record["_ts"] >= start]


def metrics(records: list[dict], minutes: int) -> dict:
    received = [r for r in records if r.get("event") == "request_received"]
    failed = [r for r in records if r.get("event") == "request_failed"]
    sent = [r for r in records if r.get("event") == "response_sent"]
    latencies = [int(r.get("latency_ms", 0)) for r in sent if r.get("latency_ms") is not None]
    costs = [float(r.get("cost_usd", 0.0)) for r in sent]
    qualities = [float(r.get("quality_score", 0.0)) for r in sent if r.get("quality_score") is not None]
    errors = Counter(r.get("error_type", "Unknown") for r in failed)
    return {
        "p50": percentile(latencies, 50),
        "p95": percentile(latencies, 95),
        "p99": percentile(latencies, 99),
        "traffic": len(received),
        "rpm": len(received) / max(1, minutes),
        "error_rate": (len(failed) / len(received) * 100) if received else 0.0,
        "errors": dict(errors),
        "cost": sum(costs),
        "tokens_in": sum(int(r.get("tokens_in", 0) or 0) for r in sent),
        "tokens_out": sum(int(r.get("tokens_out", 0) or 0) for r in sent),
        "quality": mean(qualities) if qualities else 0.0,
    }


def badge(ok: bool) -> str:
    cls = "ok" if ok else "bad"
    return f'<span class="badge {cls}">{"PASS" if ok else "ALERT"}</span>'


def build_html(values: dict, minutes: int) -> str:
    error_details = ", ".join(f"{html.escape(k)}: {v}" for k, v in values["errors"].items()) or "Không có lỗi"
    return f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Day 13 AI Observability Dashboard</title>
<style>
body{{font-family:Arial,sans-serif;margin:0;background:#f5f7fb;color:#122033}}main{{max-width:1120px;margin:auto;padding:28px}}
header{{display:flex;justify-content:space-between;gap:20px;align-items:end;margin-bottom:20px}}h1{{margin:0;font-size:28px}}.sub{{color:#61718a;font-size:14px}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}}.card{{background:#fff;border:1px solid #dfe6ef;border-radius:14px;padding:18px;min-height:150px}}
.label{{font-size:12px;font-weight:700;color:#627089;text-transform:uppercase}}.big{{font-size:30px;font-weight:800;margin:12px 0}}.meta{{font-size:13px;color:#66758d;line-height:1.5}}
.badge{{float:right;padding:5px 8px;border-radius:999px;font-size:11px;font-weight:800}}.ok{{background:#e8f8ef;color:#157446}}.bad{{background:#feecec;color:#b42318}}
.bar{{height:8px;border-radius:8px;background:#edf1f6;margin-top:14px;overflow:hidden}}.fill{{height:100%;background:#3575f6}}
footer{{margin-top:18px;color:#687991;font-size:12px}}@media(max-width:800px){{.grid{{grid-template-columns:1fr}}}}
</style>
</head>
<body><main>
<header><div><div class="label">Day 13 · Observability</div><h1>Dashboard 6 tín hiệu bắt buộc</h1><div class="sub">Nguồn: data/logs.jsonl · Cửa sổ: {minutes} phút · Threshold/SLO hiển thị trực tiếp</div></div></header>
<section class="grid">
<div class="card"><div class="label">1. Latency</div>{badge(values['p95'] <= 3000)}<div class="big">P95 {values['p95']:.0f} ms</div><div class="meta">P50 {values['p50']:.0f} ms · P99 {values['p99']:.0f} ms<br>SLO: P95 ≤ 3000 ms</div></div>
<div class="card"><div class="label">2. Traffic</div>{badge(values['traffic'] >= 1)}<div class="big">{values['traffic']} request</div><div class="meta">{values['rpm']:.2f} request/phút<br>Threshold contract: ≥ 1 request/phút</div></div>
<div class="card"><div class="label">3. Error rate</div>{badge(values['error_rate'] <= 2)}<div class="big">{values['error_rate']:.2f}%</div><div class="meta">SLO: ≤ 2%<br>Breakdown: {error_details}</div></div>
<div class="card"><div class="label">4. Cost</div>{badge(values['cost'] <= 2.5)}<div class="big">${values['cost']:.6f}</div><div class="meta">Tổng cost trong cửa sổ<br>Budget threshold: ≤ $2.5</div></div>
<div class="card"><div class="label">5. Tokens</div>{badge(values['tokens_in'] + values['tokens_out'] <= 50000)}<div class="big">{values['tokens_in'] + values['tokens_out']:,}</div><div class="meta">Input {values['tokens_in']:,} · Output {values['tokens_out']:,}<br>Threshold: ≤ 50,000</div></div>
<div class="card"><div class="label">6. Quality proxy</div>{badge(values['quality'] >= 0.75)}<div class="big">{values['quality']:.2f} / 1</div><div class="meta">Mean quality score<br>SLO: ≥ 0.75</div><div class="bar"><div class="fill" style="width:{max(0,min(100,values['quality']*100)):.0f}%"></div></div></div>
</section>
<footer>Ảnh evidence cần nhìn rõ tên panel, time range, đơn vị và threshold. Challenge K4 dùng latency threshold riêng 2000 ms để điều tra incident.</footer>
</main></body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Build local 6-panel dashboard from data/logs.jsonl")
    parser.add_argument("--logs", type=Path, default=Path("data/logs.jsonl"))
    parser.add_argument("--minutes", type=int, default=60)
    parser.add_argument("--output", type=Path, default=Path("submission/evidence/10-dashboard.html"))
    args = parser.parse_args()
    records = load_window(args.logs, args.minutes)
    values = metrics(records, args.minutes)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_html(values, args.minutes), encoding="utf-8")
    print(f"Dashboard written: {args.output}")
    print(f"Requests={values['traffic']} P95={values['p95']:.0f}ms Error={values['error_rate']:.2f}% Quality={values['quality']:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
