# Contributing to AI Health Monitoring Prototype

Thanks for your interest in contributing. This project follows practical **Nexus Spring** principles: small PRs, test-first mindset, clear ownership, and secure-by-default changes.

## Ways to Contribute

- Report bugs
- Propose features or improvements
- Improve docs and developer experience
- Submit fixes with tests

## Contribution Workflow

1. Fork and create a branch:
   - `feat/<short-description>` for features
   - `fix/<short-description>` for bug fixes
2. Set up local development using [`DEVELOPMENT.md`](./DEVELOPMENT.md).
3. Make focused changes.
4. Run quality checks locally:
   - `python -m black --check .`
   - `python -m flake8`
   - `python -m pytest -q`
5. Open a pull request using the PR template.

## Coding Standards

- Follow PEP 8 and project formatting (Black + Flake8).
- Keep functions small and explicit.
- Prefer deterministic logic for tests.
- Do not commit generated model artifacts, local data dumps, or secrets.

## Testing Expectations

- Add or update tests for behavior changes.
- Keep test scope close to the change.
- Ensure existing tests pass unless failures are unrelated and documented in the PR.

## Commit & PR Guidelines

- Use clear commit messages (imperative tense).
- Keep PRs reviewable and focused.
- Include:
  - Problem summary
  - Approach
  - Validation evidence (test/lint output)
  - Risk and rollback notes if relevant

## Security and Responsible AI

- Follow [`SECURITY.md`](./SECURITY.md) for vulnerability reporting.
- Do not include personal health data in issues, tests, or commits.
- This project is a prototype and is **not** for clinical decision-making.

## Community

By participating, you agree to follow [`CODE_OF_CONDUCT.md`](./CODE_OF_CONDUCT.md).
