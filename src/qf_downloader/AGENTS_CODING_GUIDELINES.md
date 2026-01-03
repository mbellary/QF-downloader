# AGENTS_CODING_GUIDELINES.md — Source Code Modification & Enhancement Rules

This document provides strict guidelines for how AI agents and developers
must write, update, and optimize source code in this repository.

Compliance ensures:
✔ Maintainable codebase
✔ Predictable behavior for CI & automation
✔ Style consistency across contributions

---

## 📂 Source Code Organization Rules

All production code resides under: `src/greetings_lib/`

Rules:

- One module per core logical area
- Keep functions small and single-responsibility
- Avoid circular dependencies
- Prefer clear procedural code over unnecessary abstraction

---
## 🧪 Test-Driven Development Requirements

Every meaningful change must be accompanied by:

✔ Updated tests  
✔ Additional tests if behavior expands  
✔ Test-first approach for new features

Before PR submission:

```bash
uv run pytest --cov
```
Agents must understand:
🚫 Code without tests = Not Done

## 🧹 Naming & Code Style Conventions
| Entity    | Convention       | Example                  |
| --------- | ---------------- | ------------------------ |
| Functions | snake_case       | `generate_greeting()`    |
| Modules   | snake_case       | `greetings.py`           |
| Classes   | PascalCase       | `GreetingService`        |
| Constants | UPPER_SNAKE_CASE | `DEFAULT_NAME = "World"` |

Also enforced:

* Type annotations required for all functions
* Descriptive names (avoid single-letter vars except in loops)
* Max line length: 100 chars (Ruff rule)
* No unused imports or dead code

## 🔄 Rules for Enhancing Existing Code

If modifying an existing module:

1️⃣ Read existing tests

2️⃣ Understand expected behavior

3️⃣ Evaluate whether the change introduces:

* New behavior
* Breaking behavior
* Broader design implications

4️⃣ Update tests first

5️⃣ Perform change incrementally

6️⃣ Validate local environment with:
```bash
uv run ruff format .
uv run ruff check . --fix
uv run pytest --cov
```

7️⃣ Update documentation (README + AGENTS files) if behavior changes

8️⃣ Submit PR with clear commit messages and link it to issue #.

## 🧩 Major Refactor Workflow

If changes significantly restructure code:

| Action                                |         Required        |
| ------------------------------------- | :---------------------: |
| Update tests and coverage             |            ✔            |
| Update documentation                  |            ✔            |
| Add migration note in commit body     |            ✔            |
| Deprecation handling if API changes   |            ✔            |
| Increment version in `pyproject.toml` | ✔ (semantic versioning) |


⚠️ Deprecate before removing functionality

⚠️ Clearly communicate breaking changes

## 🧪 New Feature Rules

For any new feature:

✔ Create/update tests

✔ Follow existing folder structure and naming patterns

✔ Ensure consistent interface with existing commands and CLI (worker)

✔ Validate integration with CI and Docker if applicable

## ⚠️ AI Agent Pitfalls to Avoid

🚫 Do NOT bypass linting rules

🚫 Do NOT hardcode OS-specific paths

🚫 Do NOT modify CI configuration unless absolutely necessary

🚫 Do NOT merge behavior changes without docs updates

## 🔍 Before You Commit…

AI agents must run:
```bash
uv run ruff format .
uv run ruff check . --fix
uv run pytest --cov
```
All must pass → Safe to commit


## 🧠 Essential AI Agent Decision Making Rules

When modifying code, always verify:

`“Does this maintain or improve clarity, correctness, or scope?”`

If not → Do not change the code.

`“Does this impact users or existing behavior?”`

If yes → Update tests + README + AGENTS docs.

`“Can a future agent understand these changes instantly?”`

If yes → You are doing it right.