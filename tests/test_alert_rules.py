from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_alert_rules_are_concrete_and_have_runbooks() -> None:
    config = yaml.safe_load(
        (REPO_ROOT / "config" / "alert_rules.yaml").read_text(encoding="utf-8")
    )
    alerts = config["alerts"]

    assert len(alerts) == 3
    assert {alert["severity"] for alert in alerts} == {"critical", "warning"}
    for alert in alerts:
        assert "TODO" not in str(alert)
        assert alert["type"] == "symptom-based"
        assert alert["condition"]
        assert (REPO_ROOT / alert["runbook"].split("#", 1)[0]).exists()


def test_alert_runbook_covers_all_alert_anchors() -> None:
    runbook = (REPO_ROOT / "docs" / "alerts.md").read_text(encoding="utf-8")

    for anchor in ("## Alert 1", "## Alert 2", "## Alert 3"):
        assert anchor in runbook
    assert "TODO" not in runbook


def test_slo_has_no_placeholder_target() -> None:
    slo = (REPO_ROOT / "config" / "slo.yaml").read_text(encoding="utf-8")

    assert "Replace with your group's target" not in slo
