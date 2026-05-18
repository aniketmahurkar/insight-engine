"""Governed SQL executor with multi-layer defense.

Layers:
1. Allowlist (YAML) — only permitted tables
2. Blocked columns (PII) — word-boundary matching
3. DDL/DML rejection — only SELECT allowed
4. Auto-LIMIT injection — prevents unbounded queries
5. Auto-qualification — fixes bare table names
6. Auto-fix — corrects known LLM column misnames
"""
import re
import sqlite3
from pathlib import Path
from dataclasses import dataclass
import yaml


@dataclass
class QueryResult:
    columns: list[str]
    rows: list[tuple]
    row_count: int
    query: str


class ExecutorError(Exception):
    pass


class SQLExecutor:
    BLOCKED_PATTERNS = [
        re.compile(r"\b(DROP|ALTER|CREATE|INSERT|UPDATE|DELETE|TRUNCATE|GRANT|REVOKE)\b", re.IGNORECASE),
    ]
    DEFAULT_LIMIT = 500
    MAX_LIMIT = 10000

    def __init__(self, config_dir: str):
        config_path = Path(config_dir)
        self.allowlist = self._load_yaml(config_path / "allowlist.yaml")
        self.blocked_columns = self._load_yaml(config_path / "blocked_columns.yaml")
        self.column_fixes = self._load_yaml(config_path / "column_fixes.yaml")
        self._conn = None

    def _load_yaml(self, path: Path) -> dict:
        if path.exists():
            return yaml.safe_load(path.read_text()) or {}
        return {}

    def connect(self, db_path: str):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)

    # --- Layer 5: Auto-qualification ---
    def _auto_qualify(self, sql: str) -> str:
        """Add schema prefix to bare table names based on naming convention."""
        qualifications = self.allowlist.get("auto_qualify", {})
        for prefix, schema in qualifications.items():
            pattern = re.compile(rf"\bFROM\s+({prefix}\w+)\b", re.IGNORECASE)
            sql = pattern.sub(rf"FROM {schema}.\1", sql)
            pattern = re.compile(rf"\bJOIN\s+({prefix}\w+)\b", re.IGNORECASE)
            sql = pattern.sub(rf"JOIN {schema}.\1", sql)
        return sql

    # --- Layer 6: Auto-fix known LLM mistakes ---
    def _auto_fix(self, sql: str) -> str:
        """Correct known column misnames that LLMs consistently get wrong."""
        fixes = self.column_fixes.get("replacements", {})
        for wrong, correct in fixes.items():
            sql = re.sub(rf"\b{wrong}\b", correct, sql, flags=re.IGNORECASE)
        return sql

    # --- Layer 4: Auto-LIMIT injection ---
    def _inject_limit(self, sql: str) -> str:
        """Inject LIMIT if not present."""
        if not re.search(r"\bLIMIT\s+\d+", sql, re.IGNORECASE):
            sql = f"{sql.rstrip().rstrip(';')} LIMIT {self.DEFAULT_LIMIT}"
        else:
            # Cap existing LIMIT
            match = re.search(r"\bLIMIT\s+(\d+)", sql, re.IGNORECASE)
            if match and int(match.group(1)) > self.MAX_LIMIT:
                sql = re.sub(r"\bLIMIT\s+\d+", f"LIMIT {self.MAX_LIMIT}", sql, flags=re.IGNORECASE)
        return sql

    # --- Layers 1-3: Validation ---
    def validate_query(self, sql: str) -> list[str]:
        violations = []
        # Layer 3: DDL/DML check
        for pattern in self.BLOCKED_PATTERNS:
            if pattern.search(sql):
                violations.append(f"Blocked DDL/DML: {pattern.pattern}")

        # Layer 1: Allowlist
        allowed_tables = self.allowlist.get("tables", [])
        if allowed_tables:
            from_pattern = re.compile(r"\bFROM\s+(\w+)", re.IGNORECASE)
            join_pattern = re.compile(r"\bJOIN\s+(\w+)", re.IGNORECASE)
            tables_used = set(from_pattern.findall(sql) + join_pattern.findall(sql))
            for table in tables_used:
                if table.lower() not in [t.lower() for t in allowed_tables]:
                    violations.append(f"Table '{table}' not in allowlist")

        # Layer 2: Blocked columns
        blocked = self.blocked_columns.get("columns", [])
        for col in blocked:
            if re.search(rf"\b{col}\b", sql, re.IGNORECASE):
                violations.append(f"Blocked PII column '{col}' in query")

        return violations

    def execute(self, sql: str) -> QueryResult:
        """Execute with full governance pipeline: fix → qualify → validate → limit → run."""
        sql = self._auto_fix(sql)
        sql = self._auto_qualify(sql)

        violations = self.validate_query(sql)
        if violations:
            raise ExecutorError(f"Query blocked: {'; '.join(violations)}")

        if not self._conn:
            raise ExecutorError("Not connected")

        sql = self._inject_limit(sql)
        cursor = self._conn.execute(sql)
        columns = [d[0] for d in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        return QueryResult(columns=columns, rows=rows, row_count=len(rows), query=sql)

    def close(self):
        if self._conn:
            self._conn.close()
