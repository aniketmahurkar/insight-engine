"""Post-generation validation against gold standard with tolerance bands.

Validates that computed metrics fall within acceptable tolerance of known-good values.
Tolerance bands vary by metric type (percentages tighter than counts).
"""
from dataclasses import dataclass


# Tolerance bands per metric type
TOLERANCE_BANDS = {
    "percentage": 0.02,    # ±2 percentage points
    "score": 0.05,         # ±0.05 absolute
    "count": 0.05,         # ±5% relative
    "duration": 0.05,      # ±5% relative
    "rate": 0.02,          # ±2 percentage points
}

# Map KPI codes to metric types
KPI_TYPES = {
    "VOL": "count",
    "AHT": "duration",
    "CSAT": "percentage",
    "FCR": "rate",
    "CES": "score",
}


@dataclass
class ValidationResult:
    kpi_code: str
    computed_value: float
    expected_value: float
    tolerance: float
    within_tolerance: bool
    pct_diff: float


def validate_metric(kpi_code: str, computed: float, expected: float) -> ValidationResult:
    """Validate a single metric against expected value using appropriate tolerance band."""
    metric_type = KPI_TYPES.get(kpi_code, "count")
    tolerance = TOLERANCE_BANDS.get(metric_type, 0.05)

    if metric_type in ("percentage", "rate", "score"):
        # Absolute difference for bounded metrics
        diff = abs(computed - expected)
        within = diff <= tolerance
        pct_diff = diff
    else:
        # Relative difference for unbounded metrics
        if expected == 0:
            pct_diff = 0.0 if computed == 0 else 1.0
        else:
            pct_diff = abs(computed - expected) / abs(expected)
        within = pct_diff <= tolerance

    return ValidationResult(
        kpi_code=kpi_code,
        computed_value=computed,
        expected_value=expected,
        tolerance=tolerance,
        within_tolerance=within,
        pct_diff=pct_diff,
    )


def validate_report(computed_metrics: dict[str, float], expected_metrics: dict[str, float]) -> list[ValidationResult]:
    """Validate all metrics in a report against gold standard."""
    results = []
    for code, computed in computed_metrics.items():
        if code in expected_metrics:
            results.append(validate_metric(code, computed, expected_metrics[code]))
    return results
