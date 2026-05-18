# Contributing

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the Demo
```bash
bash demo/run_demo.sh
```

## Adding a New KPI
1. Add the KPI definition to `config/kpis.yaml`
2. Ensure the source table is in `config/allowlist.yaml`
3. Test with the demo database
