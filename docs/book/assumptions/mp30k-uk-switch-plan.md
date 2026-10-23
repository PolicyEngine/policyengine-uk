# Switching the default dataset: gates and rollback

```{note}
**Planning page.** [#1692](https://github.com/PolicyEngine/policyengine-uk/issues/1692)
asked for a switch and rollback path from the Enhanced FRS (eFRS) to Microplex UK
(`mp-30k-uk`). The `microplex-uk` repository has since been archived, and its
successor is [Microcosm UK](https://github.com/PolicyEngine/microcosm), whose
UK national line publishes `microcosm_uk_2024_25.h5`. This page applies the
same switch and rollback path to Microcosm UK.
```

## Current state

PolicyEngine UK has no built-in default dataset. An inline `situation`, if
passed, is used on its own. Otherwise `Simulation()` uses, in order:

1. an explicit `dataset=` argument;
2. the `POLICYENGINE_UK_DEFAULT_DATASET` environment variable
   (`DEFAULT_DATASET_ENV_VAR` in `tax_benefit_system.py`);
3. otherwise it raises a `ValueError` (`get_default_dataset_url` in
   `simulation.py`).

When a Hugging Face token is available, the test suite sets the variable to
the certified dataset pinned by commit and SHA-256 in
`policyengine_uk/tests/certified_dataset.yaml` (read by
`policyengine_uk/tests/conftest.py`): `enhanced_frs_2024_25.h5` from
policyengine-uk-data 1.58.1, in the private
`policyengine/policyengine-uk-data-private` repository. So the eFRS is still
the dataset this repository's tests run on.

Direct microsimulation through `Microsimulation()` in this package is
deprecated in favour of [policyengine.py](https://github.com/PolicyEngine/policyengine.py),
whose managed bundle pins certified datasets (see the repository README). The
default most users meet is therefore the one that bundle pins, so a switch has
to be made there as well as in this repository's tests. policyengine.py made
that switch in release 6.10.0 (21 October 2026): its UK default is now
Microcosm UK 2024-25 (`microcosm_uk_2024_25`), and the Enhanced FRS 2024-25
stays loadable by name. Only this repository's tests remain on the eFRS.

## What the switch needs

### Loader

- `UKMultiYearDataset` and `UKSingleYearDataset`
  (`policyengine_uk/data/dataset_schema.py`) are the containers both datasets
  load into. A Microcosm file must use the same table and column conventions,
  because `_pre_encode_enum_columns` (in `simulation.py`) walks each year's
  tables.
- The dataset's `years` drive uprating. Microcosm's base year is 2024-25,
  the same as the eFRS file now used in tests (`enhanced_frs_2024_25`).
- String enum columns must use the member names in this repo's variable
  definitions (for example `OWNED_OUTRIGHT`, not "Owned outright"). An
  unknown name raises a `ValueError` when the dataset is encoded
  (policyengine-core's `Enum.encode`); integer-coded columns are not
  checked.

### Variables

- `policyengine_uk/variables/input/` holds most of the inputs, but the
  loader (`build_from_multi_year_dataset` in `simulation.py`) sets every
  dataset column named after any model variable as an input and skips the
  rest, and several dataset inputs are defined elsewhere (for example
  `tenure_type`, `household_weight` and `would_claim_uc`). A switch should
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

1. Dataset choice stays a runtime setting: no code in this repo branches on
   which dataset is loaded. One parameter is tied to the dataset, though:
   `gov.simulation.vat.survey_consumption_coverage` is calibrated to the
   Microcosm UK 2024-25 release only, puts VAT 38% to 44% above 2024-25
   receipts on the Enhanced FRS 2024-25, and has to be re-derived when the
   default dataset changes (`docs/engineering/vat-coverage.md`).
2. While both are in use, CI runs the dataset-dependent tests on both.
3. The default is set per environment through
   `POLICYENGINE_UK_DEFAULT_DATASET` (in policyengine.py, through its bundle
   manifest), with the eFRS file kept available.
4. Rolling back is changing that setting and redeploying. The only change
   needed here is re-deriving dataset-calibrated parameters such as the VAT
   coverage above. This assumes the eFRS file stays published while the
   switch beds in.

## Acceptance

PolicyEngine UK switches its default only after the gates above pass, with a
rollback that needs no code change in this repo beyond dataset-calibrated
parameters. Until then either dataset can
be used by passing `dataset=` or setting the environment variable.

## References

- Tracking issue: [#1692](https://github.com/PolicyEngine/policyengine-uk/issues/1692) (still open). Its umbrella discussion is in the archived [`microplex-uk`](https://github.com/PolicyEngine/microplex-uk/discussions/2) repository.
- Related: [#1621](https://github.com/PolicyEngine/policyengine-uk/issues/1621) (aligning the UK model and data pipeline).
- Microcosm UK: [repository](https://github.com/PolicyEngine/microcosm).
- Dataset loading: `policyengine_uk/simulation.py`, `policyengine_uk/data/dataset_schema.py`.
