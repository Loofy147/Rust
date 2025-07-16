# Development Guide

## Local Setup
- Clone the repo
- Install dependencies: `pip install -r requirements.txt`
- (Optional) Use the dev container for instant onboarding
- Install pre-commit hooks: `pre-commit install`

## Running the API
```bash
uvicorn api.main:app --reload
```

## Using the CLI
```bash
python manage.py seed           # Seed sample data
python manage.py clear          # Clear the KG database
python manage.py test           # Run all tests
python manage.py typecheck      # Run mypy type checks
python manage.py reload-plugins # Enable hot plugin reload (restart API after)
```

## Hot Plugin Reload
- Set `DEV_MODE=1` in your environment
- Restart the API to reload plugin code

## Mock Plugins & Sample Data
- Set `MOCK_PLUGINS=1` to use mock plugins
- Use `python manage.py seed` to populate the KG/vector store

## Debugging & Troubleshooting
- Use structured logs (Loguru, JSON) for easy debugging
- Check `/metrics` for Prometheus stats
- Use `/docs` for interactive API testing
- For plugin issues, use hot reload and check logs for import errors

## Advanced Workflows
- Use VSCode dev container for instant setup
- Use `pytest --cov` for coverage
- Use `mypy` and `pyright` for type safety
- Add new plugins and test with mock/sample data

## Testing & Coverage
- Run all tests: `pytest`
- Check type safety: `mypy .`
- Coverage report: `pytest --cov`

## Linting & Formatting
- Format code: `black . && isort .`
- Lint: `flake8 .`

## Type Checking
- `mypy .` (strict mode)
- `pyright` (for VSCode users)

## Contributing
See [Contributing](contributing.md) for PR and code style guidelines.