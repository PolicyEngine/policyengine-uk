Fixes #

## What and why

## Test plan

- [ ] For policy changes: YAML tests whose expected values come from an external source (legislation, official guidance, official calculator); otherwise mark not applicable.
- [ ] `make format`
- [ ] Changelog fragment in `changelog.d/`

## Reproducer

<!-- Required for fix PRs: an added or modified .fixed.md changelog fragment, or the bug/bug-fix label. Name a test in an added or modified file: a pytest node id (file.py::test_name or file.py::Class::test_name), a YAML policy test file or file.yaml::name, or n/a: <reason> for CI/docs-only fixes. Separate multiple ids with commas or semicolons. -->
Reproducer: <test id>

<!-- Required for any change to policy (programmes, parameters, eligibility, bug fixes). See .github/CONTRIBUTING.md ("Axiom parity"). Keep one standard option below, or use axiom: needed if you are an external contributor who cannot complete the Axiom work; a maintainer will follow up. -->
axiom: <legal id> encoded-correct | <rulespec-uk PR> encoded | <rulespec-uk issue> queued | n/a: <reason>
