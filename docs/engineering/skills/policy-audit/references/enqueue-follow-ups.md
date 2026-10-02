# Enqueue a related audit follow-up

Do not classify the selected unit as incorrect merely because research exposes
a discrepancy in another parameter or variable. Add a cited follow-up for the
actual target unit instead:

```yaml
follow_ups:
  - unit_id: parameter:gov.department.program.threshold
    reason_code: suspected_incorrect_in_release
    reason: The released threshold differs from the official amount.
    observed_model: The release contains £100 from April 2026.
    expected_policy: The official rates document specifies £110.
    evidence_ids: [rates-2026]
    model_locations:
      - path: policyengine_uk/parameters/gov/department/program/threshold.yaml
        location: values.2026-04-01
```

The target must exist in the same release catalog. Each model path must belong
to that target, and discrepancy-based follow-ups require official evidence from
the originating review. Recording the review creates or augments one pending
follow-up per release and target unit.

For a discrepancy discovered after the originating review was recorded, create
a standalone request with the same fields plus `release_version`,
`origin_review`, and `evidence`:

```yaml
release_version: 2.106.1
unit_id: parameter:gov.department.program.threshold
origin_review:
  unit_id: parameter:gov.department.program.rate
  audited_at: 2026-10-02
reason_code: suspected_incorrect_in_release
reason: The released threshold differs from the official amount.
observed_model: The release contains £100 from April 2026.
expected_policy: The official rates document specifies £110.
evidence_ids: [rates-2026]
model_locations:
  - path: policyengine_uk/parameters/gov/department/program/threshold.yaml
    location: values.2026-04-01
evidence:
  - id: rates-2026
    organisation: Department name
    authority_type: official rates
    title: Benefit rates 2026 to 2027
    url: https://www.gov.uk/example
    final_url: https://www.gov.uk/example
    accessed_at: 2026-10-02
    locator: Program table, threshold row
```

```bash
policy-audit enqueue-follow-up follow-up.yaml
policy-audit follow-ups --version 2.106.1
```

Recording a review of the target resolves its pending follow-up and retains the
origin and resolution history. Close a false or obsolete follow-up only with an
explicit explanation:

```bash
policy-audit close-follow-up UNIT_ID --version 2.106.1 --reason "Explanation"
```
