# Implement and publish the correction

After publishing an issue for `incorrect_in_release` or
`superseded_since_release`, implement the correction and open a draft pull
request. Do not treat publication of the issue as completion of the audit
workflow.

## Separate the audited release from the correction

- Keep the checkout for the audited release unchanged so the recorded evidence
  continues to describe that exact version.
- Apply the correction on a feature branch based on the current upstream
  default branch. Never push directly to the default branch.
- Before editing, check whether the current default branch already contains the
  correction. If it does, search all pages of open and closed pull requests and
  link the existing implementation instead of creating an empty pull request.

## Implement the reviewed parts

- Use the issue's implementation parts as the scope. If implementation reveals
  another coupled defect, correct the issue description and audit record before
  expanding the pull request.
- Add each official source to the relevant parameter value metadata or variable
  reference as described in
  [place-code-citations.md](place-code-citations.md).
- Add focused regression tests for the affected periods, household types, and
  jurisdictions. Run each new or modified test file, but do not require a full
  repository test run before publishing the draft pull request; rely on CI for
  broader regression coverage.
- Follow the repository's model structure, testing, documentation review, and
  pull request guidance. Run formatting and add the required Towncrier
  changelog fragment.

## Publish the draft pull request

- Commit and push only the feature branch.
- Open the pull request as a draft. Put `Fixes #ISSUE_NUMBER` on the first line
  of its description.
- Summarize the correction, name the official sources embedded in the model,
  and list every validation command and result.
- Verify the pull request directly after creation and record or report its URL.
  If publication fails, report the exact failure; do not describe the issue-only
  state as a completed publishable audit.
