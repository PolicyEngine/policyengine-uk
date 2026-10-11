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

## How CI Runs The Tests

Pull requests and merge queue groups (`.github/workflows/pr_code_changes.yaml`),
pushes to `main` (`code_changes.yaml`, never cancelled, and skipped for a
commit the merge queue already tested) and releases (`versioning.yaml`) all run
the same suite,
`.github/workflows/test-suite.yaml`, in the locked environment
(`uv sync --frozen --extra dev`). Pull requests and `main` test the source
tree; a release tests the wheel it is about to publish, installed on its own.

The suite runs the YAML policy tests in one job and splits the Python tests
over three runners. Each runner runs one shard:

```bash
pytest policyengine_uk/tests -n 4 --dist worksteal --shard K/3 -o xfail_strict=true
```

`--shard K/N` is defined in `policyengine_uk/tests/conftest.py`. It keeps the
tests whose node id hashes to shard K of N, so every test is in exactly one
shard, including a test added later. Each shard records every test's outcome
with `.github/pytest_outcome_log.py`. The final job, `Test / Result`, runs
`.github/check_test_shards.py`. It fails unless every collected test ran in
exactly one shard and passed. The exceptions are outcomes accepted in
`.github/test_outcome_allowlist.toml`:

- A skip, an expected failure (`xfail`), an XPASS or a skipped module fails
  the job unless an allowlist entry covers it. A test that quietly stops
  running turns CI red. For example, when the dataset credentials are missing,
  the microsimulation tests are allowed to skip only in runs that have no
  credentials.
- `xfail` markers are strict. When the bug a marker pins is fixed, the test
  fails until you remove the marker and its allowlist entry.
- A new known bug pinned by a strict `xfail` needs an allowlist entry that
  names its issue. Keep entries narrow, and remove them when they are no
  longer needed; the check warns about entries that matched nothing.

To reproduce CI's check locally on the whole suite, run `make test-ci`.

- To rerun what one CI shard ran, pass the same `--shard K/N` locally.
- To make CI faster, add a shard to the `shard` matrix in `test-suite.yaml`.
- Do not split tests by file or directory in a workflow: a test outside the
  listed paths would silently not run.
