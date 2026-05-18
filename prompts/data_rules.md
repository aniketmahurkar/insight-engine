---
priority: 4
description: Data display rules and pre-output checklist
---

# Data Rules

## Display Rules
- Time metrics: display in appropriate unit (seconds for <60, minutes for >60)
- Percentages: display as 0-100 with 1 decimal
- Always report sample sizes. Flag n < 30
- No PII in any output

## Null Handling
| Column | Rule |
|--------|------|
| duration_seconds | Exclude 0 and NULL |
| status | Treat NULL as 'unknown' |
| user_id | Exclude NULL from per-user aggregations |

## Pre-Output Checklist
- [ ] Date filters applied
- [ ] NULL handling applied
- [ ] No PII columns in output
- [ ] Sample sizes reported
- [ ] Percentages in 0-100 range (not 0.0-1.0)
