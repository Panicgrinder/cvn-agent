# History purge plan (docs-only)

Goal

- Prepare a reversible plan to remove historical mentions from docs without touching source or datasets.
- Limit scope to documentation and markdown-like files to avoid breaking tests.

Scope

- Included: `docs/**`, `README.md`, DONE/CHANGELOG-like files.
- Excluded: `eval/**`, `app/**`, `scripts/**`, any code or datasets.
- Submodule: run a separate pass inside `cvn-agent/` if needed.

Safety checklist

- Create a fresh backup/clone before rewriting history.
- Ensure all branches are locally up to date.
- Coordinate force-push windows with collaborators/CI.

Install tool

- Prefer git-filter-repo: <https://github.com/newren/git-filter-repo>
  - On Windows: `pip install git-filter-repo` or place the script on PATH.

Dry-run preview

- Use `--force` only when you are confident. Test on a throwaway clone first.

Command (root repository)

- Replace the token only in selected paths and keep other history intact.

Example

```powershell
# Docs-only path limiter (example; adapt to your needs)
$env:GFR = 'git filter-repo'
# Example: show how to keep only docs history then operate on that separate clone
Write-Host "Run in a throwaway clone to validate before pushing."
```

PowerShell helper

- See `scripts/history_purge_plan.ps1` for a guided flow (docs-only, optional message rewrite).

Submodule

- Enter `cvn-agent/` and run the same steps independently.

Push

- After validation in a separate clone, push with `--force-with-lease`.

Rollback

- If anything looks off, discard the rewritten clone and keep the original remote/history.
