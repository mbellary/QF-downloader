# AGENTS_TESTS.md — Automated Test Execution Guide

This document is for AI agents and developers working with this repository.
It defines how tests must be installed, executed, and validated both locally
and within CI to ensure consistent enforcement of code quality.

By following this specification, testing remains reliable, automated,
and consistent across all development environments.

---

## 🧰 Test Environment Setup
* Tests are written using pytest, located under tests/

This project uses:
- `tests` directory for storing test files
- `pytest` for test execution
- `pytest-cov` for coverage reporting
- `ruff` for linting + formatting checks
- `uv` for dependency and virtual environment management

### Install development dependencies

```bash
uv pip install -e ".[dev]"
```
This will create and activate .venv automatically.

Verify installation:
```bash
uv run ruff --version
```

## 🧪 Running the Tests
<!-- #### Basic test run
```bash
uv run pytest -v
```
#### Test with coverage report
```bash
uv run pytest --cov=math_lib --cov-report=term
``` -->
#### Generate coverage XML report (required by CI)
```bash
uv run pytest --cov=math_lib --cov-report=xml
```

Test files must reside under:
```bash
tests/
```

Example test path:
```bash
tests/test_math.py
```

## 🧹 Format & Lint Before Running Tests
Tests must not run unless code formatting is clean.
* See ```docs/agents/AGENTS_LINTING.md``` for details.

🚫 CI will fail if formatting or lint errors exist

## 🔄 CI / GitHub Actions Test Workflow
CI runs automatically on:

* pushes to main
* pull requests targeting main

Pipeline stages:
| Stage              | Tool                  |              Required to Pass              |
| ------------------ | --------------------- | :----------------------------------------: |
| Formatting         | `ruff format --check` |                      ✔                     |
| Linting            | `ruff check`          |                      ✔                     |
| Test Execution     | `pytest`              |                      ✔                     |
| Coverage Reporting | `pytest-cov`          |                      ✔                     |
| Coverage Upload    | Codecov (optional)    | ⚠ (soft failure allowed if tokens missing) |


## 🧪 Writing & Structuring New Tests

* Place new test files inside tests/
* Use descriptive, small, isolated unit tests
* Use **one assertion per behavior**
* Name format:
    ```bash
    test_<functionality>.py
    ```
* Example test:
    ```python
    from math_lib.math import add_numbers

    def test_add_numbers():
        assert add_numbers(2, 3) == 5
        assert add_numbers(-1, 1) == 0
    ```
* Any change in functionality → update or add tests

## ⚠️ Troubleshooting Test Issues
| Problem                                     | Solution                                                        |
| ------------------------------------------- | --------------------------------------------------------------- |
| Tests fail because imports break            | Ensure module is under `src/math_lib/`                     |
| Virtual environment not picking up packages | Run `uv pip install -e ".[dev]"` again                          |
| Ruff failures block tests                   | Fix with: `uv run ruff format . && uv run ruff check . --fix`   |
| CI failing on coverage                      | Ensure `coverage.xml` is generated or update `pytest-cov` flags |


## 📌 Requirements for PR Approval
Before opening a Pull Request:

* ✔ All tests passing locally
* ✔ Coverage does not regress
* ✔ Lint + formatting passes
* ✔ CI pipeline successful

## 🧠 For AI Agents

* Tests must always run before committing code
* Do not add test-specific dependencies that slow CI
* Maintain high coverage — aim for ≥90% wherever possible
* Update this file if workflows change