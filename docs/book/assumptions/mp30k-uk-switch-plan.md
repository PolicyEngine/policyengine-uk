# Switching the default dataset: gates and rollback

```{note}
**Planning page.** [#1692](https://github.com/PolicyEngine/policyengine-uk/issues/1692)
asked for a switch and rollback path from the Enhanced FRS (eFRS) to Microplex UK
(`mp-30k-uk`). Microplex UK has since been archived (May 2026), and its successor
is [Microcosm UK](https://github.com/PolicyEngine/microcosm). Its first
certified national release, `microcosm_uk_2024_25.h5`, is dated 4 October 2026.
This page applies the same switch and rollback path to Microcosm UK.
```

## Current state

PolicyEngine UK has no built-in default dataset. `Simulation()` uses, in order:

1. an explicit `dataset=` argument;
2. the `POLICYENGINE_UK_DEFAULT_DATASET` environment variable
   (`DEFAULT_DATASET_ENV_VAR` in `tax_benefit_system.py`);
3. otherwise, unless an inline `situation` is passed, it raises a `ValueError`
   (`get_default_dataset_url` in `simulation.py`).

The test suite sets the variable to the private
`hf://policyengine/policyengine-uk-data-private/enhanced_frs_2023_24.h5@1.40.3`
when a Hugging Face token is available (`policyengine_uk/tests/conftest.py`).
So the eFRS is still the dataset the model is tested against, and the
default in downstream tools such as policyengine.py.

## What the switch needs

### Loader

- `UKMultiYearDataset` and `UKSingleYearDataset`
  (`policyengine_uk/data/dataset_schema.py`) are the containers both datasets
  load into. A Microcosm file must use the same table and column conventions,
  because `_pre_encode_enum_columns` walks each year's tables.
- The dataset's `years` drive uprating. Microcosm's base year is 2024-25,
  one year later than the eFRS file used in tests, so uprating paths from the
  earlier base year need checking.
- Enum columns must use the labels in this repo's variable definitions.
  Unknown labels do not encode correctly.

### Variables

- `policyengine_uk/variables/input/` is the data contract. A switch should
  report the input columns present in one dataset but not the other, and
  decide for each whether a missing column is acceptable.
- Take-up and other reported-versus-simulated inputs have to come from the
  new data, not be carried over from the eFRS.

### Calibration

- Microcosm calibrates its own weights against its target register, and
  certifies each release through its own checks. The model side should
  compare results against those targets, not re-weight.

## Switch criteria

A documented gate must pass before any environment's default changes:

1. **Aggregates:** headline totals (income tax, NICs, UC, Child Benefit,
   State Pension) on both datasets for the same year, each set against OBR
   outturn, with any difference of more than £1bn or 2% (whichever is wider)
   explained.
2. **Distribution:** decile mean net income and HBAI poverty rates (before
   and after housing costs) within 2 percentage points, or explained.
3. **Reforms:** at least three standard reforms (for example +1p on the basic
   rate, +£5 a week on the UC standard allowance, abolishing the two-child
   limit) give the same sign and are within 5% of each other.
4. **Tests:** the suite passes with the new default, including
   `test_latest_data_smoke.py`, `test_deterministic_variables.py` and
   `test_no_economic_assumptions.py`.
5. **Documentation:** the `assumptions/` section records the switch and any
   remaining aggregate gaps.

## Rollback path

1. Dataset choice stays a runtime setting: no code in this repo depends on
   which dataset is loaded.
2. While both are in use, CI runs the dataset-dependent tests on both.
3. The default is set per environment through
   `POLICYENGINE_UK_DEFAULT_DATASET`, with the eFRS file kept available.
4. Rolling back is changing that variable and redeploying, with no code
   change here. This assumes the eFRS file stays published while the switch
   beds in.

## Acceptance

PolicyEngine UK switches its default only after the gates above pass, with a
rollback that needs no code change in this repo. Until then either dataset can
be used by passing `dataset=` or setting the environment variable.

## References

- Tracking issue: [#1692](https://github.com/PolicyEngine/policyengine-uk/issues/1692) (still open). Its umbrella discussion is in the archived [`microplex-uk`](https://github.com/PolicyEngine/microplex-uk/discussions/2) repository.
- Related: [#1621](https://github.com/PolicyEngine/policyengine-uk/issues/1621) (aligning the UK model and data pipeline).
- Microcosm UK: [repository](https://github.com/PolicyEngine/microcosm).
- Dataset loading: `policyengine_uk/simulation.py`, `policyengine_uk/data/dataset_schema.py`.
