# Development Guide

## Prerequisites

- Python 3.10+
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

## Daily Workflow

1. Sync latest changes from main.
2. Create a branch for your change.
3. Implement and test locally.
4. Run quality checks.
5. Open a PR with context and validation notes.

## Quality Checks

```bash
python -m black --check .
python -m flake8
python -m pytest -q
```

## Running the Prototype

```bash
python main.py generate-data --duration 1440 --interval 300
python main.py train-model
python main.py dashboard
```

## Project Layout

- `src/sensors/` sensor simulation
- `src/processing/` data pipeline utilities
- `src/models/` anomaly/risk models
- `src/dashboard/` Flask dashboard
- `tests/` unit tests
- `data/` generated datasets (local/dev)
- `models/` trained model outputs (local/dev)

## Nexus Spring Contributor Practices

- Keep PRs small and scoped to one concern.
- Prefer explicit interfaces over implicit coupling.
- Add tests for changed behavior.
- Document decisions that impact future contributors.
