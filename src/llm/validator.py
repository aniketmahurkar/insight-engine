"""Fact-checking layer: Python computes, LLM interprets only."""


def validate_claim(actual_value: float, stated_value: float, tolerance: float = 0.05) -> bool:
    if actual_value == 0:
        return stated_value == 0
    return abs(actual_value - stated_value) / abs(actual_value) <= tolerance


def validate_direction(claim_direction: str, actual_change: float) -> bool:
    if "increase" in claim_direction.lower() or "up" in claim_direction.lower():
        return actual_change > 0
    if "decrease" in claim_direction.lower() or "down" in claim_direction.lower():
        return actual_change < 0
    return True
