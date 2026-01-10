# AGENTS_ENVIRONMENT.md — Development Environment & Setup Guide

This document defines the required development environment configuration
for all AI coding agents and humans contributing to this repository.

Following this guide ensures:

✔ Code runs consistently across machines  
✔ CI validations pass automatically  
✔ Formatting, linting & tests remain reliable  
✔ Agents understand toolchain behavior  

---

## 🧰 Required Tools

| Tool | Purpose |
|------|---------|
| Python ≥ 3.11 | Runtime & development |
| uv | Virtual environments + dependency mgmt |
| git | Source control |
| Docker (optional) | Containerized workflow |
| pre-commit (optional) | Auto lint/format before commits |

Install `uv` using pip:

```bash
pip install uv
```
Verify installation:
```bash
uv --version
```
## 🛠 Setup Local Workspace
Update local workspace with remote git changes

```bash
git pull origin main && make check && make test SUITE=unit
```

Install dependencies in editable mode (required for tests + CI):

```bash
uv pip install -e ".[dev]"
```
This will automatically:

✔ Create a .venv/ virtual environment

✔ Install runtime + development dependencies

✔ Expose tools like pytest and ruff

## 🧩 UV Virtual Environment
Preferred execution pattern:
```bash
uv run <command>
```
Example:
```bash
uv run pytest -v
```

## 🔄 Feature Branch Setup
* See `.github/BRANCH/branch.md` for details on branching
* $short-task-name MUST be replaced with the correct task name.

```bash
git switch -c task/$short-task-name
```

## 🏗 Project Structure Overview
```bash
QF-downloader/
├─ .github/
│  ├─ agents/
│  ├─ workflows/
│  ├─ BRANCH/
│  ├─ PULL_REQUEST/
│  ├─ AGENTS_COLLABORATION.md
│  ├─ auto_assign.yml
│  └─ CODEOWNERS
├─ docker/
│  └─ docker-compose.test.yml
├─ docs/
│  └─ quant/
│     ├─ data_providers/
│     ├─ target_schemas/
│     └─ (spec + schema docs)
├─ plans/
│  ├─ p0_1_raw_market_data_ingestion/
│  ├─ p0_2_macro_news_ingestion/
│  ├─ p0_4_integration_tests/
│  └─ p0_4_unit_tests/
├─ src/
│  └─ qf_downloader/
│     ├─ __init__.py
│     ├─ aws_clients.py
│     ├─ cli.py
│     ├─ config.py
│     ├─ db.py
│     ├─ downloader.py
│     ├─ logger.py
│     ├─ provider_config.py
│     ├─ s3_indexer.py
│     ├─ storage.py
│     ├─ utils.py
│     ├─ providers.yaml
│     ├─ providers_single_pair.yaml
│     ├─ .env.dev
│     ├─ .env.prod
│     ├─ AGENTS_CODING_GUIDELINES.md
│     └─ AGENTS_LINTING.md
├─ targets/
│  ├─ alpha_dir_label_metadata.json
│  ├─ macro_event_metadata.json
│  ├─ microstructure_schema.json
│  └─ path_label_metadata.json
├─ tests/
│  ├─ integration/
│  ├─ unit/
│  └─ AGENTS_TESTS.md
├─ Agents.md
├─ AGENTS_ENVIRONMENT.md
├─ base_prompt.txt
├─ coverage.xml
├─ data_tasks.md
├─ docker-compose.yml
├─ docker-compose.test.yml
├─ Dockerfile.dev
├─ Dockerfile.prod
├─ Dockerfile.test
├─ Makefile
├─ PLANS.md
├─ prometheus.yml
├─ pyproject.toml
├─ pytest.ini
├─ README.md
├─ TEST_README.md
└─ uv.lock
```
Rules:

* All Python source lives under src/qf_downloader/

Agents must preserve this layout.

## 🧹 Developer Setup Checklist
Run these after installation:
```bash
make check && make test SUITE=unit
```
If failures occur → fix locally before committing.

## 🔁 Pre-commit Hook Installation (Strongly Recommended)
```bash
uv run pre-commit install
```
This ensures:

✔ Ruff auto-formatting

✔ Lint fixes applied

✔ No broken code enters history

## 🔒 CI Parity Requirements
Local environment must match CI expectations:
| Requirement            | Verified by           |
| ---------------------- | --------------------- |
| Lint clean             | `ruff check`          |
| No format drift        | `ruff format --check` |
| Tests passing          | `pytest`              |
| Coverage XML available | `pytest-cov`          |

🚫 If any check fails locally → PR will fail CI


## 🧠 Rules for AI Agents

* Never run tooling outside uv (avoid global pip installs)
* Never commit code without lint + format compliance
* Keep virtual environment inside project root
* Update this document when environment policy changes

## Summary Commands
| Action                  | Command                      |
| ----------------------- | ---------------------------- |
| Install dev environment | `uv pip install -e ".[dev]"` |
| Run app                 | `worker World`               |
| Run tests               | `uv run pytest`              |
| Lint + auto-fix         | `uv run ruff check . --fix`  |
| Format code             | `uv run ruff format .`       |
| Dev Docker run          | `docker compose run dev`     |
