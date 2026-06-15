# Contributing to AI Health Monitoring Prototype

Thank you for your interest in contributing.

## Project Vision
This project demonstrates AI-assisted health monitoring using simulated wearable data. Contributions should improve reliability, reproducibility, and developer experience while keeping safety messaging clear.

## How to Contribute
1. Fork the repository and create a feature branch.
2. Make focused, minimal changes.
3. Add or update tests when behavior changes.
4. Run local checks before opening a pull request.
5. Open a PR using the provided template.

## Local Quality Checks
```bash
pip install -r requirements.txt
pytest -q
flake8 .
black --check .
```

## Coding Standards
- Follow PEP 8 style and keep functions small and readable.
- Prefer explicit names over abbreviations.
- Avoid introducing breaking changes without discussion.
- Keep health/safety disclaimers intact in user-facing docs.

## Commit and PR Guidelines
- Use descriptive commit messages.
- Keep each PR scoped to one logical change.
- Include context, motivation, and validation steps.
- Link related issues (for example: `Closes #12`).

## Reporting Bugs and Requesting Features
Use the issue templates in `.github/ISSUE_TEMPLATE/` so maintainers can triage quickly.

## Review Process
Maintainers review for:
- Correctness and safety messaging
- Test coverage and validation
- Documentation quality
- Scope and maintainability

## Getting Help
- Open a discussion or issue for design questions.
- For security concerns, do **not** open a public issue. Follow `SECURITY.md`.
