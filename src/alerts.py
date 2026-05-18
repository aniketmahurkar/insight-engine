"""Analyzes metrics_log.jsonl to detect recurring anomaly patterns.

Identifies KPIs flagged N+ consecutive runs — signals systemic issues
vs one-off spikes.
"""
import json
from pathlib import Path


def analyze_recurring_flags(log_path: str, min_consecutive: int = 3) -> list[dict]:
    """Find KPIs flagged in N+ consecutive report runs."""
    path = Path(log_path)
    if not path.exists():
        return []

    entries = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if not entries:
        return []

    streak: dict[str, int] = {}
    alerts = []

    for entry in entries:
        flagged_codes = {k["code"] for k in entry.get("flagged_kpis", [])}

        # Update streaks
        for code in list(streak.keys()):
            if code in flagged_codes:
                streak[code] += 1
            else:
                streak.pop(code)
        for code in flagged_codes:
            if code not in streak:
                streak[code] = 1

    for code, count in streak.items():
        if count >= min_consecutive:
            # Get latest anomaly details
            latest = next(
                (k for entry in reversed(entries) for k in entry.get("flagged_kpis", []) if k["code"] == code),
                {}
            )
            alerts.append({
                "code": code,
                "consecutive_flags": count,
                "latest_z_score": latest.get("z_score"),
                "direction": latest.get("direction"),
            })

    return alerts


if __name__ == "__main__":
    import sys
    log_path = sys.argv[1] if len(sys.argv) > 1 else "metrics_log.jsonl"
    alerts = analyze_recurring_flags(log_path)
    if alerts:
        print("⚠️  Recurring anomalies detected:")
        for a in alerts:
            print(f"  {a['code']}: flagged {a['consecutive_flags']} consecutive runs "
                  f"(z={a['latest_z_score']}, {a['direction']})")
    else:
        print("✓ No recurring patterns")
