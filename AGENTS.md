# Agent Instructions

These instructions apply repository-wide.

## Canonical Guidance

Canonical AI-facing engineering guidance lives under
`docs/engineering/skills/`. Use those files as the source of truth across
Codex, Claude, Copilot, and other AI tools.

Tool-specific instruction files such as `CLAUDE.md` and
`.github/copilot-instructions.md` should stay thin and point here instead of
duplicating repository rules.

## Required Skill Lookup

Before opening, replacing, or sharing a pull request, read
`docs/engineering/skills/github-prs.md`.

When adding, moving, or reviewing tests, read
`docs/engineering/skills/testing.md`.

When adding or changing variables, parameters, reforms, enums, or program
metadata, read `docs/engineering/skills/model-structure.md`.

When changing simulation dataset loading, default datasets, H5 inputs, or
interactions with upstream dataset materializers, read
`docs/engineering/skills/dataset-sources.md`.

When changing public behavior, documentation, metadata surfaces, or generated
documentation, read `docs/engineering/skills/documentation-review.md`.

## Non-Negotiable PR Requirements

Every pull request must include a Towncrier changelog fragment under
`changelog.d/`. See `docs/engineering/skills/github-prs.md` for the naming and
type rules.

Run lint and formatting before committing. The default command is `make format`.
