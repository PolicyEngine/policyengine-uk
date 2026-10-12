# GitHub Pull Requests

Use this skill before opening, replacing, updating, or sharing a pull request.
Follow `.github/CONTRIBUTING.md` and the shared PolicyEngine contribution guide
linked from it. This file adds AI-specific routing and does not replace those
requirements.

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

Use a stable issue number or branch slug before the configured Towncrier type:

```text
changelog.d/<issue-number-or-branch-slug>.<type>.md
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

## Fix evidence

The **Fix evidence** pull request check applies when a PR adds, modifies or
type-changes a fixed fragment directly in `changelog.d/`, or has the `bug` or
`bug-fix` label. A fragment counts as fixed when its basename has `fixed` in
any dot-separated part after the first, including `x.fixed.md`, `x.fixed.1.md`,
`x.fixed.md.md` and `x.fixed`. Use the canonical fragment naming convention
above when writing new fragments. A fix PR must add, modify or type-change an
executable test under `policyengine_uk/tests/` and name its reproducer in the
PR description:

```text
Reproducer: policyengine_uk/tests/path/to/test_file.py::test_name
```

Accepted ids are pytest node ids (`file.py::test_name` or
`file.py::TestClass::test_name`) and YAML policy tests under
`policyengine_uk/tests/policy/` (`file.yaml` or `file.yaml::test name`, also
accepting `.yml`). Each named file must be added, modified or type-changed in
the PR. Python files must match `test_*.py` or `*_test.py`, and names must
resolve to module-level functions starting with `test`, or methods starting
with `test` in module-level classes starting with `Test`. Such a class may
derive only from `object` or `unittest.TestCase` (also as `TestCase` imported
from `unittest`) and may not define `__init__` or `__new__`. A module or class whose `__test__` is anything but
`True`, a test or class whose `__test__` attribute is set after it is defined,
a fixture, and definitions nested in functions or conditional blocks are
excluded. The reproducer must run and pass: a `skip` or `xfail` mark, or
unittest's `skip` or `expectedFailure`, on it, its class or its module
(`pytestmark`) is rejected. A `skipif` condition must hold false in CI, so the
reproducer runs there, and the test must not skip itself at run time
(`pytest.skip`, `pytest.importorskip`), which the check cannot see. A test marked
`microsimulation` runs only where the dataset is available, which includes
merge-queue and main runs. YAML files must parse to a non-empty list with at
least one mapping containing a string `name` and a non-empty `output` mapping;
a named YAML reproducer must match such a mapping exactly.
Separate multiple ids with commas or semicolons. Backticks around each id
are optional; use them when a name or reason contains these separators.
Reproducer lines inside HTML comments are ignored.

For CI/docs-only fixes, use `Reproducer: n/a: <reason>` with a non-empty reason.
This exempts the PR from changing a test only when no file under
`policyengine_uk/` outside `policyengine_uk/tests/` is added, modified,
type-changed or deleted, and neither `pyproject.toml` nor `uv.lock` changes.
Dependency changes can change model results, so they also require a test.
The workflow runs the trusted base-branch checker and reads test files from
the PR head's git objects, rejecting symlinked test paths. It validates the
named reproducer without running PR code or testing against the old code.

## Required Axiom Line

Every PR that adds, updates or fixes policy (programmes, parameters, eligibility
rules, bug fixes) must also leave the same provision correct in
[rulespec-uk](https://github.com/TheAxiomFoundation/rulespec-uk). State which of
these applies in one line of the PR description:

```text
axiom: <legal id> encoded-correct | <rulespec-uk PR> encoded | <rulespec-uk issue> queued | n/a: <reason>
```

If you are an external contributor and cannot complete the Axiom work, use
`axiom: needed`; a maintainer will follow up.

Use `queued` only when the signed encoder is blocked; record the blocker in the
issue. Each billed encoder run requires separate approval. A `queued`
rulespec-uk issue must be dispatch-ready and labelled `pe-parity`. It needs the
module path and corpus citation, the verbatim law, the required outputs, and
companion tests from the same external source as the PR's YAML tests. Never
hand-write RuleSpec. See `.github/CONTRIBUTING.md` ("Axiom parity").

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
