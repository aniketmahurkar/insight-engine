# insight-engine

**Your automated KPI report in 3 minutes instead of 8 hours.**

An autonomous analysis agent that connects to any SQL warehouse, detects anomalies via z-scores and trend breaks, investigates root causes through multi-turn LLM reasoning, and generates executive reports with full audit trails.

Works for any data domain — SaaS metrics, e-commerce KPIs, infrastructure monitoring, financial data, or any time-series you track.

## Quick Start

```bash
git clone https://github.com/aniketmahurkar/insight-engine.git
cd insight-engine
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run demo (no API key needed — uses fallback mode)
bash demo/run_demo.sh
```

## Architecture

See [docs/architecture.md](docs/architecture.md) for full technical documentation.

```
insight-engine/
├── src/                    # Core engine
│   ├── analyzer.py         # 3-phase pipeline (parallel pre-fetch → investigate → report)
│   ├── executor.py         # Multi-layer governed SQL executor
│   ├── anomaly.py          # Z-score, trend break, WoW detection
│   ├── reporter.py         # Report builder
│   ├── validator.py        # Tolerance-band validation
│   ├── alerts.py           # Recurring anomaly detection
│   └── llm/                # LLM integration
├── config/                 # Governance (allowlists, KPI definitions)
├── prompts/                # Stakeholder-editable context
├── roles/                  # LLM persona definitions
├── demo/                   # One-command demo
└── docs/                   # Architecture documentation
```

## How It Prevents Hallucinations

1. **Python computes, LLM interprets** — All numbers from SQL, not LLM
2. **Evidence rules** — Forbidden speculative language, required data references
3. **6-layer SQL governance** — auto-fix → auto-qualify → DDL block → allowlist → PII block → auto-LIMIT
4. **Tolerance-band validation** — Different thresholds per metric type
5. **JSONL metrics log** — Cross-report meta-analysis detects recurring patterns

## Configuration

Define your KPIs in YAML:
```yaml
kpis:
  - name: "Transaction Volume"
    code: "VOL"
    daily_sql: "SELECT event_date, COUNT(*) as val FROM events WHERE ..."
    date_field: "event_date"
```

## Supported Warehouses

SQLite (demo) | PostgreSQL | Trino | Snowflake | BigQuery

## LLM Providers

Uses [litellm](https://github.com/BerriAI/litellm) — OpenAI, Anthropic, Gemini, local models. Without an API key, runs in fallback mode (anomaly detection + template reports).

## License

MIT
