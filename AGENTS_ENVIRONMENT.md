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
## 🛠 Project Installation
<!-- Clone the repository:
```bash
git clone https://github.com/mbellary/math-lib.git
cd math-lib
``` -->
Install dependencies in editable mode (required for tests + CI):
```bash
uv pip install -e ".[dev]"
```
This will automatically:

✔ Create a .venv/ virtual environment

✔ Install runtime + development dependencies

✔ Expose tools like pytest and ruff

## 🧩 Virtual Environment
Ensure environment is active before running commands:
```bash
source .venv/bin/activate
```
(uv normally handles this automatically when using uv run)
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
│─ .github/
│   ├─ workflows/
│   │   └─ full_pipeline.yml
│   ├─ BRANCH/
│   │   └─ branch.md
│   ├─ PULL_REQUEST/
│   │   └─ pull_request.md
│   ├─ agents/
│   │   ├─ Assistant.agent.md
│   │   ├─ Data Engineering Architect.agent.md
│   │   ├─ Program Manager.agent.md
│   │   └─ Tester.agent.md
│   ├─ AGENTS_COLLABORATION.md
│   ├─ auto_assign.yml
│   └─ CODEOWNERS
├─ docs/
│   └─ quant/
│       ├─ README.md
│       ├─ FROZEN.md
│       ├─ schema_registry.yaml
│       ├─ data_providers/
│       └─ target_schemas/
├─ plans/
│   ├─ p0_1_raw_market_data_ingestion/
│   │   └─ p0_1_raw_market_data_ingestion_execplan.md
│   └─ p0_2_macro_news_ingestion/
│       └─ p0_2_macro_news_ingestion_execplan.md
├─ src/
│   └─ qf_downloader/
│       ├─ __init__.py
│       ├─ cli.py
│       ├─ config.py
│       ├─ db.py
│       ├─ downloader.py
│       ├─ downloader_test.py
│       ├─ s3_indexer.py
│       ├─ storage.py
│       ├─ utils.py
│       ├─ providers.yaml
│       ├─ providers_single_pair.yaml
│       ├─ AGENTS_CODING_GUIDELINES.md
│       └─ AGENTS_LINTING.md
├─ data/
├─ docker/
│   └─ docker-compose.test.yml
├─ targets/
│   ├─ alpha_dir_label_metadata.json
│   ├─ macro_event_metadata.json
│   ├─ microstructure_schema.json
│   └─ path_label_metadata.json
├─ docker-compose.yml
├─ docker-compose.test.yml
├─ Dockerfile.dev
├─ Dockerfile.prod
├─ Dockerfile.test
├─ prometheus.yml
├─ pyproject.toml
├─ pytest.ini
├─ uv.lock
├─ README.md
├─ Agents.md
└─ AGENTS_ENVIRONMENT.md
```
Rules:

* All Python source lives under src/qf_downloader/
* Tests currently live alongside source (e.g. src/qf_downloader/downloader_test.py)

Agents must preserve this layout.

## 🧹 Developer Setup Checklist
Run these after installation:
```bash
uv run ruff format .         # auto-format code
uv run ruff check .          # lint
uv run pytest --cov          # run tests with coverage
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
