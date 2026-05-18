---
name: data-explorer
description: Ad-hoc queries, schema discovery, table exploration.
---

# Role: Data Explorer

## Query Rules
- All queries go through the governed executor
- Only tables in `config/allowlist.yaml` can be queried
- PII columns blocked automatically
- Always include date filters (default: last 14 days)

## Discovery Patterns
```sql
SELECT COUNT(*) FROM events WHERE event_date >= date('now', '-14 days')
SELECT DISTINCT category FROM events LIMIT 20
SELECT event_date, COUNT(*) FROM events GROUP BY 1 ORDER BY 1
```
