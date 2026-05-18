"""Multi-turn LLM investigator with 2-round JSON array investigation pattern.

Round 1: LLM reviews anomaly, generates up to 6 targeted queries
Round 2: LLM reviews Round 1 results, drills deeper with up to 6 more queries
Final: LLM synthesizes findings into root cause summary
"""
import json
import re
from pathlib import Path
from ..anomaly import AnomalyResult
from ..executor import SQLExecutor, ExecutorError
from .prompts import build_investigation_prompt, build_followup_prompt

try:
    import litellm
    HAS_LLM = True
except ImportError:
    HAS_LLM = False

MAX_ROUNDS = 2
MAX_QUERIES_PER_ROUND = 6


class Investigator:
    def __init__(self, config_dir: str, model: str = "gpt-4o"):
        self.model = model
        self.config_dir = Path(config_dir)

    def investigate(self, kpi_name: str, anomaly: AnomalyResult, executor: SQLExecutor) -> str:
        if not HAS_LLM:
            return self._fallback(kpi_name, anomaly)

        all_findings = []

        # Round 1: Initial investigation
        prompt = build_investigation_prompt(kpi_name, anomaly)
        queries_r1 = self._get_investigation_queries(prompt)
        results_r1 = self._execute_queries(queries_r1, executor)
        all_findings.extend(results_r1)

        # Round 2: Follow-up based on Round 1 results
        if results_r1:
            followup_prompt = build_followup_prompt(kpi_name, anomaly, results_r1)
            queries_r2 = self._get_investigation_queries(followup_prompt)
            results_r2 = self._execute_queries(queries_r2, executor)
            all_findings.extend(results_r2)

        # Synthesize
        return self._synthesize(kpi_name, anomaly, all_findings)

    def _get_investigation_queries(self, prompt: str) -> list[dict]:
        """Ask LLM for investigation queries in JSON array format."""
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "Respond with a JSON array of investigation queries."},
        ]
        try:
            response = litellm.completion(model=self.model, messages=messages, temperature=0.1)
            raw = response.choices[0].message.content
            # Extract JSON array (tolerates markdown wrapping)
            match = re.search(r'\[.*\]', raw, re.DOTALL)
            if match:
                queries = json.loads(match.group())
                return queries[:MAX_QUERIES_PER_ROUND]
        except Exception:
            pass
        return []

    def _execute_queries(self, queries: list[dict], executor: SQLExecutor) -> list[dict]:
        """Execute investigation queries, return results with context."""
        results = []
        for q in queries:
            sql = q.get("sql", "")
            gap = q.get("gap", "unknown")
            if not sql:
                continue
            try:
                result = executor.execute(sql)
                results.append({
                    "gap": gap,
                    "sql": sql,
                    "data": result.rows[:10],
                    "columns": result.columns,
                    "row_count": result.row_count,
                })
            except ExecutorError as e:
                results.append({"gap": gap, "sql": sql, "error": str(e)})
        return results

    def _synthesize(self, kpi_name: str, anomaly: AnomalyResult, findings: list[dict]) -> str:
        """Synthesize findings into root cause summary."""
        if not HAS_LLM or not findings:
            return self._fallback(kpi_name, anomaly)

        data_summary = "\n".join(
            f"- {f['gap']}: {f.get('data', f.get('error', 'no data'))}"
            for f in findings
        )
        messages = [{
            "role": "system",
            "content": (
                f"You are analyzing a {kpi_name} anomaly (z-score: {anomaly.z_score:.1f}, "
                f"direction: {anomaly.direction}). Based on the investigation data below, "
                f"provide a concise root cause summary.\n\nData:\n{data_summary}\n\n"
                f"Rules: State facts only. No speculative language."
            ),
        }]
        try:
            response = litellm.completion(model=self.model, messages=messages, temperature=0.1)
            return response.choices[0].message.content
        except Exception:
            return self._fallback(kpi_name, anomaly)

    def _fallback(self, kpi_name: str, anomaly: AnomalyResult) -> str:
        return (
            f"**{kpi_name}** z-score: {anomaly.z_score:.1f} ({anomaly.direction}). "
            f"Current: {anomaly.current_value:.2f}, baseline: {anomaly.baseline_mean:.2f}. "
            f"Manual investigation recommended."
        )
