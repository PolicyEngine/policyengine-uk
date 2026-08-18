# GitHub Pull Requests

Use this skill before opening, replacing, updating, or sharing a pull request.

## Branch And Issue Flow

- Branch from an up-to-date `main`.
- Open or identify a GitHub issue for the work before opening a PR.
- Put `Fixes #ISSUE_NUMBER` as the first line of the PR description.
- Open PRs as drafts unless a maintainer explicitly asks for a ready-for-review
  PR.
- Do not add `[codex]`, `[claude]`, `[copilot]`, or other agent labels to PR
  titles. Use a plain descriptive title.

## Required Changelog Fragment

Every PR must include a Towncrier changelog fragment under `changelog.d/`.

Preferred naming:

```text
changelog.d/<issue-number>.<type>.md
```

Use one of the configured Towncrier types from `pyproject.toml`:

- `breaking`
- `added`
- `changed`
- `fixed`
- `removed`

Examples:

```text
changelog.d/1748.added.md
changelog.d/1748.fixed.md
```

Write the fragment as a short bullet describing the user-visible or maintainer
visible change:

```markdown
- Added model-agnostic AI engineering guidance for UK model work.
```

The versioning workflow runs on pushes to `main` that touch `changelog.d/**` or
`pyproject.toml`. It runs `.github/bump_version.py`, then `towncrier build`.
Do not manually edit `CHANGELOG.md` or bump `pyproject.toml` in an ordinary PR
unless the user or maintainer explicitly asks. The type controls the inferred
version bump: `breaking` is major, `added` and `removed` are minor, and other
types are patch.

## Required Lint And Format

Run lint and formatting before committing. The default command is:

```bash
make format
```

`make format` runs `ruff format .` and `ruff check .`.

If the full command is blocked by local environment constraints, run the exact
equivalent on the touched files and state that exception in the PR or handoff:

```bash
ruff format <changed-files>
ruff check <changed-files>
```

Do not knowingly commit unformatted code or known lint failures.

## Test Expectations

Run focused tests that cover the changed behavior. Use `make test` for broad
model changes, shared behavior, or changes where a narrower command would miss
important regressions. See `testing.md` for details.

When tests are skipped because they are slow, data-dependent, or require
credentials, say so explicitly in the PR description or handoff.
