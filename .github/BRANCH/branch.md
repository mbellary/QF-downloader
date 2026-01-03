# Branch Naming & Workflow Guide

All work must be done in a branch **derived from `main`** — never commit directly to main.

---

## ✍️ Branch Naming Convention

```markdown
<type>/<short-description>
```

✔ Allowed types:

| Type | When to use |
|------|-------------|
| feature | New functionality |
| fix | Bug correction |
| docs | Documentation changes |
| refactor | Internal code improvements |
| test | Test-only additions |

---

## 🧩 Examples

| Situation | Good Branch Name |
|----------|-----------------|
| Add uppercase flag to CLI | `feature/uppercase-cli-flag` |
| Fix bug with numeric inputs | `fix/numeric-inputs-cli` |
| Update README badges | `docs/update-badges` |
| Improve greet() structure | `refactor/greet-cleanup` |
| Add missing coverage tests | `tests/add-cli-tests` |
|Raw data ingetsion | `task/raw-data-ingestion` |
---

## 📌 Creating a branch

```bash
git checkout -b feature/uppercase-cli-flag
```

---

## 📌 Issue
Add or update the branch details as a comment in the issue.

---

## 🔁 Development workflow inside branch
```bash
uv run ruff format .
uv run ruff check . --fix
uv run pytest --cov
git commit -m "feat: add uppercase flag to CLI"
git push -u origin feature/uppercase-cli-flag
```

<!-- ## 🔀 PR merging rules

* Squash and Merge only
* PR must reference the Issue (Fixes #ID)
* Delete branch after merge

✔ Keeps clean commit history

✔ Ensures traceability to issue -->

## 🚫 Do NOT

* Use vague names (test123, patch1)
* Create branches without linked issue
* Merge failing CI
* Push breaking changes without docs
* commit directly to `main`.