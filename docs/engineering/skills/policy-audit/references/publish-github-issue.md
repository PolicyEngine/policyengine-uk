# Publish a cited GitHub issue

Render the issue before publication:

```bash
policy-audit render-issue review.yaml
```

The issue must contain a cited summary, visible release and unit metadata,
findings, implementation parts, code citation placements, affected periods,
and jurisdictions. Do not add hidden identifiers.

Publish only the validated structured review:

```bash
policy-audit publish-issue review.yaml --repository PolicyEngine/policyengine-uk
```

The publisher checks a previously recorded issue directly and fetches every
page of open and closed issues. It compares the exact title, release version,
and visible audit-unit identifier before creating anything. If the direct and
exhaustive results disagree, stop and reconcile them rather than creating a
second issue.
