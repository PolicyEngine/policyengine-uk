# Classify and record findings

Use one conclusion:

- `current`: no discrepancy was found on the audit date.
- `incorrect_in_release`: the selected release conflicts with the rule that
  applied to it.
- `superseded_since_release`: a later official change is absent.
- `announced_not_enacted`: official policy was announced but has not taken
  legal effect.
- `insufficient_evidence`: available official sources do not support a firm
  conclusion.
- `not_official_policy_rule`: the unit is an input, assumption, statistical
  construct, or other item that cannot be verified as a policy rule.
- `program_mapping_required`: ownership must be resolved before research can be
  reported accurately.

An issue is normally created only for `incorrect_in_release` and
`superseded_since_release`. Publication of `announced_not_enacted` requires an
explicit option.

The structured review must contain:

- `release_version`, `unit_id`, `audited_at`, and `conclusion`;
- a one-paragraph `summary` and `summary_evidence_ids`;
- non-empty `periods_reviewed` and `jurisdictions`;
- structured official `evidence`;
- findings, implementation parts, and code citation targets when a change is
  required; and
- an `issue_title` for publishable conclusions.

Validate and record it:

```bash
policy-audit validate review.yaml
policy-audit record review.yaml
```

Validation proves structural completeness and approved source locations. It
does not replace substantive legal review.

## Review shape

```yaml
release_version: 2.106.1
unit_id: parameter:gov.department.program.amount
audited_at: 2026-10-02
conclusion: superseded_since_release
summary: >-
  One paragraph explaining the encoded rule, the official change, and why the
  selected release requires an update.
summary_evidence_ids: [source-1]
periods_reviewed: [2025-26, 2026-27]
jurisdictions: [United Kingdom]
issue_title: "Update Program amount for 2026-27"
evidence:
  - id: source-1
    organisation: Department name
    authority_type: legislation
    title: "Instrument title, regulation 4"
    url: https://www.legislation.gov.uk/example
    final_url: https://www.legislation.gov.uk/example
    accessed_at: 2026-10-02
    locator: regulation 4
findings:
  - statement: The release omits the amount effective from April 2026.
    evidence_ids: [source-1]
    implementation_parts:
      - description: Add the April 2026 amount and effective date.
        evidence_ids: [source-1]
        code_reference_targets:
          - path: policyengine_uk/parameters/gov/department/program/amount.yaml
            location: values.2026-04-01.metadata.reference
            evidence_ids: [source-1]
uncertainties: "Optional, precise statement of evidence or scope limitations."
```
