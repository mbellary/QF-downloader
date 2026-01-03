---
applyTo: "**/*.md"
---


# AGENTS_COLLABORATION.md — GitHub Workflow for Branches, Issues & PRs

This document defines how AI agents and developers collaborate using GitHub.  
It ensures that contributions are traceable, reviewable, and CI-compliant.


---
## 🧭 Collaboration Goals

✔ Clean and readable Git history  
✔ Traceability from Issue → Branch → PR → Merge  
✔ No broken code reaches `main`  
✔ Ensures continuous deployment readiness

---

## 📝 1️⃣ Issue Workflow

All changes must start with an Issue.

Steps:

1. Search existing issues to avoid duplicates
2. Create a new issue if needed, including:
   - **Title:** Clear and concise
   - **Body:** Problem + Proposed solution + Acceptance criteria
   - **Labels:** `bug`, `feature`, `docs`, `tech-debt`

3. Assign priority and milestone if known

Issue format example:

As a <user/agent>
I want <feature or fix>
So that <value provided>

* See `.github/ISSUE/bug.md` for details on bug request.
* See `.github/ISSUE/feature.md` for details on feature request.

---

## 🌱 2️⃣ Branch Strategy
* See `.github/BRANCH/branch.md` for details on branching.

## 💬 3️⃣ Commit Message Guidelines
Commit messages must follow this structure:
```template
<type>: <short summary>

<details and context if needed>
Fixes #<issue-number>
```
Allowed commit types:
| Type     | Purpose                                   |
| -------- | ----------------------------------------- |
| feat     | New functionality                         |
| fix      | Bug fix                                   |
| docs     | Documentation only                        |
| refactor | Code improvement without behavior changes |
| test     | Test-related                              |
| chore    | Build/CI/support tasks                    |

Good example:
```template
feat: add CLI argument parsing for worker
Fixes #42
```

## 🔀 4️⃣ Pull Request Guidelines
* See `.github/PULL_REQUEST/pull_request.md` for details on pull request.

## 🧠 AI Agent Rulebook

Before pushing:
```bash
uv run ruff format .
uv run ruff check . --fix
uv run pytest --cov
```

A PR must reflect:

* Minimal changes that deliver maximum improvement
* Clear intent + traceable issue linkage
* Consistency with project structure and style

## 🧾 Summary Workflow
| Stage         | Command / Action                       |
| ------------- | -------------------------------------- |
| Create issue  | Document context + acceptance criteria |
| Create branch | `git checkout -b feature/...`          |
| Dev workflow  | Format → Lint → Test                   |
| Push branch   | `git push -u origin <branch>`          |
| Create PR     | Link Issue + pass CI                   |
<!-- | Review        | Apply requested changes                |
| Merge         | Squash + delete branch                 | -->
