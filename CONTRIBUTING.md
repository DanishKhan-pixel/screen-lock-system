# Contributing to Aegis

Thank you for taking the time to contribute! Please follow these guidelines to keep the project tidy and the review process smooth.

## Development Setup

```bash
git clone <repo-url> && cd screen-lock-system
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in your local DB credentials
python manage.py migrate
python manage.py seed_demo    # optional demo data
python manage.py runserver
```

## Branching Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Stable, production-ready code |
| `dev`  | Integration branch for reviewed features |
| `feature/<name>` | Individual feature development |
| `fix/<name>` | Bug fixes |

Always branch from `dev`. Open a pull request targeting `dev`.

## Commit Messages

Follow the **Conventional Commits** spec:

```
<type>(<scope>): <short summary>
```

Common types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.  
Examples:
- `feat(accounts): add PIN expiry support`
- `fix(middleware): handle Resolver404 for unknown paths`
- `docs: update README setup instructions`

## Code Style

- Python: follow [PEP 8](https://peps.python.org/pep-0008/). Use `ruff` for linting.
- Templates: keep logic minimal; move complex logic to views or template tags.
- Tests: add or update tests for every non-trivial change.

## Running Tests

```bash
python manage.py test
```

## Pull Request Checklist

- [ ] Tests pass locally
- [ ] New behaviour is covered by tests
- [ ] CHANGELOG.md updated under `[Unreleased]`
- [ ] Commit messages follow Conventional Commits
