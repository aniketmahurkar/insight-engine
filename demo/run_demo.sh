#!/bin/bash
set -e
cd "$(dirname "$0")/.."

echo "=== Insight Engine Demo ==="
echo ""
echo "Step 1: Seeding demo database..."
python3 demo/seed_demo_db.py

echo ""
echo "Step 2: Running analysis pipeline..."
python3 demo/run_analysis.py

echo ""
echo "Done! Report saved to reports/report.md"
