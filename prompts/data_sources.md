---
priority: 3
description: Available data sources and schema reference
---

# Data Sources

## events
Primary fact table for system/business events.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| event_date | TEXT | Date of event (YYYY-MM-DD) |
| category | TEXT | api, web, mobile, batch |
| user_id | INTEGER | User identifier |
| duration_seconds | INTEGER | Processing duration |
| status | TEXT | success, error, timeout |

## users
User dimension table.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| segment | TEXT | free, pro, enterprise |
| created_date | TEXT | Account creation date |

## metrics
Pre-computed metric aggregations.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| event_date | TEXT | Date |
| metric_name | TEXT | Name of the metric |
| value | REAL | Metric value |
