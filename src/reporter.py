"""Report generator — outputs markdown with audit trail."""
from datetime import datetime
from pathlib import Path


class ReportBuilder:
    def __init__(self, output_path: str):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.sections: list[str] = []
        self.audit_trail: list[dict] = []

    def add_header(self, title: str):
        self.sections.append(f"# {title}\n\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")

    def add_section(self, title: str, content: str):
        self.sections.append(f"## {title}\n\n{content}\n")

    def add_table(self, headers: list[str], rows: list[list[str]]):
        header_line = "| " + " | ".join(headers) + " |"
        separator = "| " + " | ".join(["---"] * len(headers)) + " |"
        data_lines = ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
        self.sections.append(f"{header_line}\n{separator}\n" + "\n".join(data_lines) + "\n")

    def add_bullets(self, items: list[str]):
        self.sections.append("\n".join(f"- {item}" for item in items) + "\n")

    def add_audit_entry(self, metric: str, query: str, result: str):
        self.audit_trail.append({"metric": metric, "query": query, "result": result})

    def save(self):
        content = "\n".join(self.sections)
        if self.audit_trail:
            content += "\n## Audit Trail\n\n"
            for e in self.audit_trail:
                content += f"**{e['metric']}**\n```sql\n{e['query']}\n```\nResult: {e['result']}\n\n"
        self.output_path.write_text(content)
