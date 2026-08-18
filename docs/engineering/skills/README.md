# Engineering Skills

This directory is the canonical source for AI-facing engineering rules.

Tool-specific instruction files such as `AGENTS.md`, `CLAUDE.md`, and
`.github/copilot-instructions.md` should point here instead of duplicating
implementation-specific guidance. When a rule changes, update the skill here
first, then keep adapters thin.

Current skills:

- `dataset-sources.md`: default datasets, HuggingFace dataset URLs, local H5
  file paths, and upstream dataset materialization behavior.
- `documentation-review.md`: model-neutral review checks for public behavior,
  docs, metadata, and generated documentation.
- `github-prs.md`: issue-first PR workflow, required Towncrier changelog
  fragments, draft PR expectations, and pre-commit lint/format rules.
- `model-structure.md`: UK variables, parameters, reforms, enums, program
  registry metadata, and refactoring recovery lessons.
- `testing.md`: UK test layout, focused test selection, slow microsimulation
  boundaries, and expected commands.

Use the narrowest skill that matches the task. When a task spans multiple
areas, read each relevant skill before editing.
