# Contributing to AI Health Monitoring Prototype

Thank you for helping improve this project. We welcome bug fixes, docs improvements, tests, and feature ideas that support safe, educational AI-health prototyping.

## Project Vision
This repository demonstrates wearable-health monitoring concepts using simulated sensor data and ML models. Contributions should prioritize:
- Reliability and reproducibility
- Clear, maintainable code
- Safety-first communication (no medical claims)

## How You Can Contribute
- Report bugs
- Propose features
- Improve docs and examples
- Add tests or strengthen validation
- Improve code quality and developer experience

## Before You Start
1. Read [README.md](README.md)
2. Set up local dev using [DEVELOPMENT.md](DEVELOPMENT.md)
3. Search existing issues/PRs to avoid duplicate work

## Development Workflow
1. Fork and clone the repository
2. Create a branch (`feature/short-description` or `fix/short-description`)
3. Make focused changes
4. Run local checks:
   ```bash
   pytest -q
   flake8 .
   black --check .
   ```
5. Update docs/tests when behavior changes
6. Open a Pull Request using the PR template

## Coding Standards
- Follow PEP 8 and keep functions focused
- Prefer explicit names over abbreviations
- Keep modules cohesive and avoid unrelated refactors
- Add/adjust tests when changing behavior
- Preserve prototype safety disclaimers

## Commit and PR Guidelines
- Write clear commit messages in imperative tense
- Keep PRs small and reviewable
- Describe **what changed**, **why**, and **how it was tested**
- Link related issues (e.g., `Closes #12`)

## Review Expectations
PRs are reviewed for:
- Correctness and scope
- Test coverage and reproducibility
- Readability and maintainability
- Security and safety considerations

Thanks for contributing!
