# Testing

Use this skill whenever adding, moving, or reviewing tests.

## Test Layout

- Policy YAML tests live under `policyengine_uk/tests/policy/` and are run with
  `policyengine-core test`.
- Python tests live under `policyengine_uk/tests/`.
- Full microsimulation tests live under `policyengine_uk/tests/microsimulation/`
  and should use the `microsimulation` marker when they exercise expensive
  survey-wide behavior.

## Choosing The Right Test

- For a variable formula or parameter rule, prefer a small YAML policy test
  first.
- For Python helper behavior, routing logic, error handling, or regression tests
  that do not need the full dataset, use focused Python tests.
- For simulation behavior that depends on survey-wide data, add the smallest
  microsimulation test that proves the behavior and mark it appropriately.
- Avoid adding slow dataset-dependent tests when a stubbed or fixture-scale test
  proves the same contract.
- Do not use real network credentials, Hugging Face downloads, GCS downloads, or
  private H5 files in unit-style tests. Mock those seams or skip cleanly when the
  external artifact is unavailable.

## Commands

Run lint and formatting before committing:

```bash
make format
```

Run every new or modified Python test file:

```bash
uv run pytest policyengine_uk/tests/path/to/test_file.py -v
```

Run every new or modified policy YAML test file:

```bash
uv run policyengine-core test policyengine_uk/tests/policy/path/to/test.yaml -c policyengine_uk
```

Do not require the full repository test suite before committing or opening a
pull request. CI provides broader regression coverage. Run `make test`, a
directory-wide test command, or microsimulation tests only when the user asks
for them or when diagnosing a failure that cannot be reproduced with the new or
modified test files.

When a new or modified test file contains several cases, run the whole file so
unchanged cases in that file also validate the shared setup. Record any test
command that was not run to completion and why.

Run a new or modified microsimulation test file explicitly:

```bash
uv run pytest policyengine_uk/tests/microsimulation/path/to/test_file.py -v
```
