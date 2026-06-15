# Development Guide

## Prerequisites
- Python 3.8+
- pip
- Git

## Local Setup
```bash
git clone https://github.com/0rb1n/AI-Health-Monitoring-Prototype.git
cd AI-Health-Monitoring-Prototype
pip install -r requirements.txt
```

## Common Commands
### Run tests
```bash
pytest -q
```

### Lint and formatting checks
```bash
flake8 .
black --check .
```

### Run CLI workflow
```bash
python main.py generate-data --duration 1440 --interval 300
python main.py train-model
python main.py dashboard
```

## Recommended Workflow
1. Create a branch from `main`.
2. Implement a single focused change.
3. Validate locally.
4. Update documentation if behavior or setup changed.
5. Open a pull request with a clear summary.

## Project Structure
```
.
├── .github/
│   ├── ISSUE_TEMPLATE/
│   ├── workflows/
│   └── PULL_REQUEST_TEMPLATE.md
├── src/
│   ├── dashboard/
│   ├── models/
│   ├── processing/
│   └── sensors/
├── tests/
├── data/
├── models/
├── notebooks/
├── CONTRIBUTING.md
├── DEVELOPMENT.md
├── SECURITY.md
├── CHANGELOG.md
├── README.md
└── main.py
```

## Safety Reminder
This repository is a prototype and must not be used for real medical diagnosis or treatment.
