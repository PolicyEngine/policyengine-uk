# Claude Instructions

These instructions apply repository-wide.

## Canonical Guidance

Repository-wide AI-facing engineering guidance lives in `AGENTS.md`.
Canonical skills live under `docs/engineering/skills/`.

Use those files as the source of truth. This file is a Claude adapter and should
stay thin; do not duplicate detailed testing, CI, formatting, pull request,
dataset, or model-structure rules here.

## Required Skill Lookup

Before opening, replacing, or sharing a PR, read
`docs/engineering/skills/github-prs.md`.

When adding, moving, or reviewing tests, read
`docs/engineering/skills/testing.md`.

When modifying variables, parameters, reforms, enums, program metadata, or UK
model structure, read `docs/engineering/skills/model-structure.md`.

When modifying simulation dataset loading, default datasets, H5 inputs, or
upstream materialized dataset paths, read
`docs/engineering/skills/dataset-sources.md`.

When changing public behavior, metadata, docs, or generated docs, read
`docs/engineering/skills/documentation-review.md`.

## Safety Boundaries

Do not fabricate policy sources, validation metrics, or performance claims. If a
result has not been computed from code or cited from a source, mark it as
pending.

Do not upload, promote, publish, or overwrite data artifacts unless the user
explicitly asks for that operation.
