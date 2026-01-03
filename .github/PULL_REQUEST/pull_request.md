# Pull Request conventions and workflow

PR requirements:

✔ Linked issue (ex: “Fixes #42”)

✔ All tests passing locally

✔ Ruff lint + formatting clean

✔ Small, focused change

✔ Clear description of intent

✔ Screenshots if behavioral change affects CLI/UI

Open PR:
```bash
git push -u origin feature/add-cli-args
```
Then open PR:

* Source: feature branch

* Target: development

Checklist included in PR description:
- [ ] Linked issue
- [ ] Tests passing
- [ ] Lint + format checks passing
- [ ] Code reviewed
- [ ] No breaking changes (unless documented)
