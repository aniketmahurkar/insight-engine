---
name: code-editor
description: Python module writing, SQL refactoring, CI/CD compliance.
---

# Role: Code Editor

## Module Organization
```
src/
├── analyzer.py      # Pipeline orchestrator
├── executor.py      # SQL governance + execution
├── anomaly.py       # Statistical detection
├── reporter.py      # Report generation
├── validator.py     # Post-generation validation
├── alerts.py        # Recurring pattern detection
└── llm/
    ├── investigator.py  # Multi-turn investigation
    ├── prompts.py       # Prompt engineering
    └── validator.py     # Fact-checking layer
```

## Code Style
- PEP 8, type hints on public functions
- Dataclasses over plain dicts
- No hardcoded paths — use config files
