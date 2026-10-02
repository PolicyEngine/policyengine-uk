---
name: audit-policyengine-uk
description: Audit a variable or grouped parameter in an exact policyengine-uk release, research its program context against official UK government sources, record the result, and open a fully cited issue when the release is incorrect or outdated.
---

# Audit PolicyEngine UK policy rules

Use the `policy-audit` command for release selection, queue state, context
construction, review validation, and GitHub publication. Do not choose a work
item manually when the request is to audit the next item, edit audit state by
hand, or send unvalidated prose directly to GitHub.

An audit conclusion describes the evidence found on the audit date. It never
asserts that a rule will remain current until a later date.

## Workflow

1. Read [select-work-item.md](references/select-work-item.md), check out the
   requested release, and claim the next unit.
2. Read [define-program-context.md](references/define-program-context.md), then
   generate and inspect the bounded context for the claimed unit.
3. Read [research-official-sources.md](references/research-official-sources.md)
   and research both the encoded rule and subsequent changes.
4. If the research identifies a discrepancy in a different audit unit, read
   [enqueue-follow-ups.md](references/enqueue-follow-ups.md) and create a cited
   follow-up without misclassifying the selected unit.
5. Read [classify-findings.md](references/classify-findings.md) and write the
   structured review.
6. If a change is needed, read
   [place-code-citations.md](references/place-code-citations.md) and identify
   where every supporting source belongs in the model source.
7. Validate and record the review. For a publishable conclusion, read
   [publish-github-issue.md](references/publish-github-issue.md) before opening
   the issue.

Do not modify model variables or parameters during this workflow. The output is
an audit record and, when justified, an issue describing the required changes.
