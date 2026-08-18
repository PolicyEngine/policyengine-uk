# Documentation Review

Use this skill when reviewing changes to public behavior, metadata surfaces,
documentation, generated docs, or repository guidance.

## Review Goal

Documentation review is a harness check, not copyediting. Confirm that durable
documentation still describes the code paths a maintainer or AI agent would use
to understand, validate, or modify the model.

Keep durable facts in source documentation. Put PR-specific confidence, impact,
or reviewer notes in the PR description or review comments instead.

## Trigger Areas

Run documentation review when a PR changes:

- public simulation behavior;
- variable or parameter behavior that changes user-visible policy results;
- `policyengine_uk/programs.yaml`;
- dataset source handling or default dataset behavior;
- generated or published docs under `docs/`;
- API-facing metadata consumed by downstream applications;
- AI-facing engineering guidance under `AGENTS.md`, `CLAUDE.md`,
  `.github/copilot-instructions.md`, or `docs/engineering/skills/`.

## Checks

- Changed public behavior has a durable documentation surface when needed.
- Program metadata remains consistent with variables, parameters, and tested
  year coverage.
- Dataset behavior docs distinguish manifest selection, remote materialization,
  and UK H5 loading.
- Generated docs are refreshed when source changes require it.
- Changelog fragments describe the change clearly and use the correct
  Towncrier type.
- PR descriptions list commands run and any skipped tests or known gaps.

## Commands

Run formatting before committing:

```bash
make format
```

Run documentation build checks when docs behavior changes materially:

```bash
make documentation
```

If a documentation command is not run because the change is guidance-only or the
local environment cannot build the docs, state that explicitly.
