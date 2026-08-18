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
- Do not use real network credentials, HuggingFace downloads, GCS downloads, or
  private H5 files in unit-style tests. Mock those seams or skip cleanly when the
  external artifact is unavailable.

## Commands

Run lint and formatting before committing:

```bash
make format
```

Run all tests when the change has broad model risk:

```bash
make test
```

Run a focused Python test:

```bash
uv run pytest policyengine_uk/tests/path/to/test_file.py::test_name -v
```

Run a focused policy YAML test:

```bash
uv run policyengine-core test policyengine_uk/tests/policy/path/to/test.yaml -c policyengine_uk
```

Run microsimulation tests explicitly:

```bash
make test-microsimulation
```

When a command is not run, record why.
