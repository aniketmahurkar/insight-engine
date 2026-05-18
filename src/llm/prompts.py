"""System prompts with evidence rules and context injection."""
from pathlib import Path
from ..anomaly import AnomalyResult

EVIDENCE_RULES = """
EVIDENCE RULES (MANDATORY):
- FORBIDDEN: "could be attributed to", "may indicate", "possibly due to", "might suggest"
- REQUIRED format: [Metric] [direction] by [amount] because [specific cause from data]
- Every claim must reference specific data (row counts, percentages, date ranges)
- If inconclusive: state "Data does not support a definitive root cause"
"""

QUERY_RULES = """
QUERY RULES:
- Only SELECT statements allowed
- Always include date filter
- Use LIMIT (max 500 rows)
- Do not query PII columns
- Max {max_queries} queries per round
"""


def load_context(config_dir: str) -> str:
    prompts_dir = Path(config_dir).parent / "prompts"
    if not prompts_dir.exists():
        return ""
    context_parts = []
    for filename in ["analysis_guidelines.md", "kpi_dictionary.md", "data_sources.md"]:
        filepath = prompts_dir / filename
        if filepath.exists():
            content = filepath.read_text().strip()
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    content = parts[2].strip()
            context_parts.append(f"## {filename.replace('.md', '').replace('_', ' ').title()}\n\n{content}")
    return "\n\n".join(context_parts)


def build_investigation_prompt(kpi_name: str, anomaly: AnomalyResult) -> str:
    return f"""You are an autonomous data investigator.

ANOMALY DETECTED:
- KPI: {kpi_name}
- Current Value: {anomaly.current_value:.2f}
- Baseline Mean: {anomaly.baseline_mean:.2f}
- Z-Score: {anomaly.z_score:.1f}
- Direction: {anomaly.direction}

AVAILABLE TABLES:
- events (id, event_date, category, user_id, duration_seconds, status)
- users (id, segment, created_date)
- metrics (id, event_date, metric_name, value)

{EVIDENCE_RULES}
{QUERY_RULES.format(max_queries=6)}

TASK: Generate investigation queries to identify the root cause.
Respond with a JSON array: [{{"gap": "what you're investigating", "sql": "SELECT ..."}}]
Maximum 6 queries. Focus on dimension breakdowns (category, segment, date) to isolate the anomaly."""


def build_followup_prompt(kpi_name: str, anomaly: AnomalyResult, round1_results: list[dict]) -> str:
    results_summary = "\n".join(
        f"- {r['gap']}: {r.get('row_count', 0)} rows, sample: {r.get('data', [])[:3]}"
        for r in round1_results if "error" not in r
    )
    return f"""Continuing investigation of {kpi_name} anomaly (z={anomaly.z_score:.1f}, {anomaly.direction}).

ROUND 1 RESULTS:
{results_summary}

{EVIDENCE_RULES}
{QUERY_RULES.format(max_queries=6)}

Generate follow-up queries to drill deeper.
Respond with a JSON array: [{{"gap": "what you're investigating", "sql": "SELECT ..."}}]"""
