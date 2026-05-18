"""Anomaly detection: z-scores, trend breaks, and week-over-week comparison."""
from dataclasses import dataclass
import statistics


@dataclass
class AnomalyResult:
    metric: str
    current_value: float
    baseline_mean: float
    baseline_stddev: float
    z_score: float
    is_anomaly: bool
    direction: str


def compute_zscore(values: list[float], current: float, threshold: float = 3.0) -> AnomalyResult:
    if len(values) < 2:
        return AnomalyResult("", current, current, 0, 0, False, "flat")
    mean = statistics.mean(values)
    stddev = statistics.stdev(values)
    if stddev == 0:
        return AnomalyResult("", current, mean, 0, 0, False, "flat")
    z = (current - mean) / stddev
    return AnomalyResult(
        metric="", current_value=current, baseline_mean=mean,
        baseline_stddev=stddev, z_score=z, is_anomaly=abs(z) > threshold,
        direction="up" if z > 0 else "down",
    )


def detect_trend_break(values: list[float], window: int = 7) -> bool:
    if len(values) < window * 2:
        return False
    prior = values[-(window * 2):-window]
    recent = values[-window:]
    prior_trend = prior[-1] - prior[0]
    recent_trend = recent[-1] - recent[0]
    return (prior_trend > 0 and recent_trend < 0) or (prior_trend < 0 and recent_trend > 0)


def week_over_week(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0
    return ((current - previous) / abs(previous)) * 100
