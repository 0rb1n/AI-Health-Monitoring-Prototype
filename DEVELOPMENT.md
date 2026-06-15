# Development Guide

This guide helps contributors set up and work on the project locally.

## Prerequisites
- Python 3.8+
- pip
- Git

## Local Setup
```bash
git clone https://github.com/0rb1n/AI-Health-Monitoring-Prototype.git
cd AI-Health-Monitoring-Prototype
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Local Validation
```bash
pytest -q
flake8 .
black --check .
```

## Running the Prototype
```bash
# Sensor stream simulation
python src/sensors/simulator.py

# Model training
python src/models/train_model.py

# Dashboard
python src/dashboard/app.py
```

## Suggested Daily Workflow
1. Sync your fork/branch
2. Create a focused branch
3. Implement change + tests/docs
4. Run local validation commands
5. Open PR with clear summary and testing notes

## Project Structure
```
.
├── src/
│   ├── sensors/            # Sensor simulation and stream generation
│   ├── models/             # Anomaly and risk model logic
│   ├── processing/         # Validation and metric processing
│   └── dashboard/          # Flask dashboard/UI
├── tests/                  # Unit tests
├── data/                   # Generated/sample data assets
├── models/                 # Saved model artifacts
├── .github/
│   ├── ISSUE_TEMPLATE/     # Bug/feature issue templates
│   ├── workflows/          # CI workflows
│   └── PULL_REQUEST_TEMPLATE.md
├── README.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
└── CHANGELOG.md
```
