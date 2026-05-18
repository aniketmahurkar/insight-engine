"""Demo analysis runner."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.analyzer import Analyzer

def main():
    project_root = Path(__file__).parent.parent
    db_path = str(project_root / "demo" / "demo.db")
    config_dir = str(project_root / "config")
    output_path = str(project_root / "reports" / "report.md")

    analyzer = Analyzer(config_dir=config_dir, db_path=db_path)
    result = analyzer.run(output_path=output_path)
    print(f"Report generated: {result}")

if __name__ == "__main__":
    main()
