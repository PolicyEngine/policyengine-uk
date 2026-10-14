Fixes #

## What and why

## Test plan

- [ ] For policy changes: YAML tests whose expected values come from an external source (legislation, official guidance, official calculator); otherwise mark not applicable.
- [ ] `make format`
- [ ] Changelog fragment in `changelog.d/`

## Reproducer

<!-- Required for fix PRs: an added, modified or type-changed fragment directly in changelog.d/ whose filename has a fixed part after the first dot, or the bug/bug-fix label. Name a collectable pytest test (file.py::test_name or file.py::TestClass::test_name) or executable YAML policy test (file.yaml or file.yaml::name) in an added, modified or type-changed file. Use n/a: <reason> only if no files under policyengine_uk/ outside policyengine_uk/tests/ and neither pyproject.toml nor uv.lock are added, modified, type-changed or deleted. Separate multiple ids with commas or semicolons. -->
Reproducer: <test id>

<!-- Required for any change to policy (programmes, parameters, eligibility, bug fixes). See .github/CONTRIBUTING.md ("Axiom parity"). Keep one standard option below, or use axiom: needed if you are an external contributor who cannot complete the Axiom work; a maintainer will follow up. -->
axiom: <legal id> encoded-correct | <rulespec-uk PR> encoded | <rulespec-uk issue> queued | n/a: <reason>
