---
priority: 1
description: Guidelines for autonomous analysis reports
---

# Analysis Guidelines

## Report Structure
1. Executive Summary (2-3 sentences, key anomalies only)
2. KPI Scorecard (deterministic table — never LLM-generated)
3. Root Cause Analysis (per anomaly, evidence-backed)
4. Recommendations (specific, actionable, time-bound)

## Narrative Rules
- Lead with the "so what" — impact before detail
- Quantify everything: "AHT increased 44%" not "AHT increased significantly"
- Compare to baseline, not arbitrary thresholds
- One root cause per paragraph, with supporting data

## Forbidden Patterns
- Do not attribute causation without data evidence
- Do not recommend "further investigation" as a standalone action
- Do not use hedge words (may, might, could, possibly, potentially)
- Do not repeat the same finding in multiple sections
