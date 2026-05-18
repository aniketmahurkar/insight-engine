"""Main 3-phase pipeline with parallel pre-fetch and 2-round LLM investigation."""
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import yaml

from .executor import SQLExecutor, ExecutorError
from .anomaly import compute_zscore, AnomalyResult
from .reporter import ReportBuilder
from .llm.investigator import Investigator

logger = logging.getLogger(__name__)

PREFETCH_WORKERS = 6
QUERY_TIMEOUT = 30
BATCH_TIMEOUT = 120


@dataclass
class KPIConfig:
    name: str
    code: str
    daily_sql: str
    date_field: str


class Analyzer:
    def __init__(self, config_dir: str, db_path: str | None = None):
        self.config_dir = Path(config_dir)
        self.kpis = self._load_kpis()
        self.executor = SQLExecutor(config_dir)
        if db_path:
            self.executor.connect(db_path)
        self.investigator = Investigator(config_dir)
        self.metrics_log_path = self.config_dir.parent / "metrics_log.jsonl"

    def _load_kpis(self) -> list[KPIConfig]:
        kpi_file = self.config_dir / "kpis.yaml"
        if not kpi_file.exists():
            return []
        data = yaml.safe_load(kpi_file.read_text())
        return [
            KPIConfig(name=k["name"], code=k["code"],
                      daily_sql=k["daily_sql"], date_field=k.get("date_field", "event_date"))
            for k in data.get("kpis", [])
        ]

    def phase1_prefetch(self) -> dict[str, AnomalyResult]:
        """Parallel KPI data fetch + anomaly detection."""
        queries = {}
        for kpi in self.kpis:
            queries[f"{kpi.code}_hist"] = (kpi, kpi.daily_sql.format(lookback="30", offset="2"))
            queries[f"{kpi.code}_curr"] = (kpi, kpi.daily_sql.format(lookback="1", offset="0"))

        results: dict[str, list] = {}
        with ThreadPoolExecutor(max_workers=PREFETCH_WORKERS) as pool:
            futures = {}
            for key, (kpi, sql) in queries.items():
                futures[pool.submit(self._safe_execute, sql)] = key
            for future in as_completed(futures, timeout=BATCH_TIMEOUT):
                key = futures[future]
                try:
                    results[key] = future.result(timeout=QUERY_TIMEOUT)
                except (TimeoutError, Exception) as e:
                    logger.warning(f"Query {key} failed: {e}")
                    results[key] = []

        anomalies = {}
        for kpi in self.kpis:
            hist = results.get(f"{kpi.code}_hist", [])
            curr = results.get(f"{kpi.code}_curr", [])
            values = [float(r[1]) for r in hist if r[1] is not None]
            if curr and curr[0][1] is not None and len(values) >= 7:
                current = float(curr[0][1])
                result = compute_zscore(values, current)
                result.metric = kpi.name
                if result.is_anomaly:
                    anomalies[kpi.code] = result
        return anomalies

    def _safe_execute(self, sql: str) -> list[tuple]:
        try:
            return self.executor.execute(sql).rows
        except ExecutorError as e:
            logger.warning(f"Execution error: {e}")
            return []

    def phase2_investigate(self, anomalies: dict[str, AnomalyResult]) -> dict[str, str]:
        """2-round LLM investigation for each anomaly."""
        investigations = {}
        for code, anomaly in anomalies.items():
            kpi = next((k for k in self.kpis if k.code == code), None)
            if not kpi:
                continue
            investigations[code] = self.investigator.investigate(kpi.name, anomaly, self.executor)
        return investigations

    def phase3_report(self, anomalies: dict, investigations: dict, output_path: str):
        """Hybrid report: deterministic tables + LLM narrative."""
        builder = ReportBuilder(output_path)
        builder.add_header("Insight Report")

        if anomalies:
            builder.add_section("Executive Summary", f"Detected **{len(anomalies)} anomalies** requiring attention.")
            headers = ["KPI", "Current", "Baseline", "Z-Score", "Direction"]
            rows = [[a.metric, f"{a.current_value:.2f}", f"{a.baseline_mean:.2f}",
                     f"{a.z_score:.1f}", a.direction] for a in anomalies.values()]
            builder.add_table(headers, rows)
        else:
            builder.add_section("Executive Summary", "All KPIs within normal range.")

        for code, anomaly in anomalies.items():
            builder.add_section(f"{anomaly.metric} ({code})",
                f"Current: {anomaly.current_value:.2f} | Baseline: {anomaly.baseline_mean:.2f} | Z: {anomaly.z_score:.1f} ({anomaly.direction})")
            if code in investigations:
                builder.add_section("Root Cause Analysis", investigations[code])

        builder.save()
        self._log_metrics(anomalies)
        return output_path

    def _log_metrics(self, anomalies: dict[str, AnomalyResult]):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "anomalies_detected": len(anomalies),
            "flagged_kpis": [{"code": c, "z_score": round(a.z_score, 2), "direction": a.direction}
                            for c, a in anomalies.items()],
        }
        try:
            with open(self.metrics_log_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    def run(self, output_path: str = "reports/report.md") -> str:
        anomalies = self.phase1_prefetch()
        investigations = self.phase2_investigate(anomalies)
        return self.phase3_report(anomalies, investigations, output_path)
