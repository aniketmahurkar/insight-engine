---
priority: 2
description: KPI calculation rules
---

# KPI Calculation Dictionary

## Transaction Volume (VOL)
- Formula: COUNT(*) of events per day
- Gotchas: Deduplication may be needed if events have retry records

## Average Processing Time (APT)
- Formula: AVG(duration_seconds) where duration > 0
- Gotchas: Exclude zero-duration events (system artifacts)
- Display in seconds or minutes depending on scale

## Success Rate (SR)
- Formula: % of events with status = 'success'
- Gotchas: Exclude events still in-progress (status = 'pending')

## Error Rate (ERR)
- Formula: % of events with status = 'error'
- Gotchas: Distinguish between client errors and server errors if possible

## Rules
- Always filter by event_date (no full-table scans)
- Exclude test/synthetic data if identifiable
- Use LOD pattern: aggregate per-entity first, then across period
