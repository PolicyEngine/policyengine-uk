# Microplex UK (mp-30k-uk) switch and rollback plan

```{note}
**Planning page.** PolicyEngine UK currently runs on the **enhanced FRS**
(eFRS, published as `policyengine/policyengine-uk-data`).
[Microplex UK](https://github.com/PolicyEngine/microplex-uk) (`mp-30k-uk`)
is the next-generation calibrated microdata. This page captures the
model-side switch and rollback path tracked under
[#1692](https://github.com/PolicyEngine/policyengine-uk/issues/1692).
```

## Current state

PolicyEngine UK accepts any HDF5 URL as its dataset. The selected
dataset URL is resolved in this order:

1. An explicit `dataset=` argument passed to `Simulation()` /
   `Microsimulation()` (see
   [`policyengine_uk/simulation.py`](../../../policyengine_uk/simulation.py)).
2. The `POLICYENGINE_UK_DEFAULT_DATASET` environment variable.
3. Otherwise the simulation requires either an inline `situation` or a
   `ValueError` is raised.

There is **no compiled-in default** — the model is dataset-agnostic by
design, and the URL is resolved at runtime. Today's typical
configuration uses
`hf://policyengine/policyengine-uk-data/enhanced_frs_2022_23.h5` (public)
or
`hf://policyengine/policyengine-uk-data-private/enhanced_frs_2023_24.h5`
(private, used in CI).

## What the switch needs

Identify eFRS-specific assumptions before switching the runtime default
to mp-30k-uk:

### Loader-side

- [`UKMultiYearDataset`](https://github.com/PolicyEngine/policyengine-core/blob/main/policyengine_core/data/dataset.py)
  is the multi-year data container used by both eFRS and (planned)
  mp-30k-uk. Confirm that mp-30k-uk's HDF5 layout matches the
  table/column conventions PolicyEngine UK reads (`_pre_encode_enum_columns`
  walks `table_names`).
- The `years` set on the dataset object drives uprating; mp-30k-uk
  needs to advertise the same year range eFRS does (or a documented
  superset).
- Enum-typed columns must use the same possible-values labels as the
  variable definitions in this repo — otherwise the `encode()` step
  silently drops rows.

### Variable-side

- The variables under
  [`policyengine_uk/variables/input/`](../../../policyengine_uk/variables/input)
  are the data-side contract. mp-30k-uk should populate all of them, or
  the variable formulas should provide sensible defaults when a column
  is missing.
- Variables that read from the dataset by name (`person("foo", data_year)`)
  break if `foo` is renamed; an audit script that reports `input/`
  columns present in eFRS but not in mp-30k-uk (and vice versa) should
  be part of the gating tests.
- The reported-vs-derived split for benefits (`_reported` inputs feeding
  formulas) means take-up will have to be re-calibrated on mp-30k-uk
  rather than carried across from eFRS.

### Calibration-side

- `policyengine-uk-data`'s reweighting routines and target sets need to
  be either pointed at mp-30k-uk inputs or retained as separate eFRS-only
  artefacts. The target set itself (HMRC + DWP outturn) doesn't change;
  what changes is the population the weights are reconciling.

## Switch criteria

A documented gate must pass before flipping the runtime default. Minimum
checklist:

1. **Aggregate parity** — `Microsimulation` totals for the headline
   tax/benefit variables (income tax, NI, UC, child benefit, state
   pension) match between eFRS and mp-30k-uk at within ±£1 bn or 2%,
   whichever is wider, against the same OBR outturn target year.
2. **Cross-section parity** — household-level decile-by-decile mean net
   income and poverty rates (HBAI + AHC) agree within 2 pp.
3. **Reform parity** — at least three canonical reforms (e.g. abolish
   council tax, +1 ppt basic rate, +£5 UC standard allowance) produce
   the same sign and within-5% magnitude of household impact on both
   datasets.
4. **Tests** — the full test suite in `policyengine_uk/tests/` passes
   against an mp-30k-uk default. Specifically, `test_no_economic_assumptions.py`,
   `test_deterministic_variables.py`, and
   `test_latest_data_smoke.py` need updating to dual-run.
5. **Documentation** — the `assumptions/` section calls out the switch
   and the residual aggregate gaps (if any) with the same level of
   detail the State Pension undershoot doc carries.

## Rollback path

Until the criteria above are met (and even after), keep eFRS as an
explicit incumbent comparator:

1. The runtime resolver in `simulation.py` stays URL-agnostic — no
   compile-time switch on the dataset identity.
2. Continuous integration runs the full test suite **on both datasets**
   while mp-30k-uk is on beta; gating any merge on parity tests
   completing on both.
3. The default URL captured in
   `POLICYENGINE_UK_DEFAULT_DATASET` becomes a deploy-time decision
   per environment (staging vs production), with eFRS as the fallback
   in every environment.
4. If a production-side mp-30k-uk regression is identified, the rollback
   is reverting that one env var and re-deploying — no code change in
   this repo. The infrastructure assumption is that
   `policyengine-uk-data` keeps publishing eFRS artefacts in parallel
   throughout the beta period.

## Acceptance

> PolicyEngine UK can switch to mp-30k-uk only after the gates above pass,
> with a tested rollback path that requires no code change in this repo.

Until then both datasets remain first-class — choose either by passing
`dataset=...` or setting the env var.

## References

- Umbrella discussion: [`PolicyEngine/microplex-uk` discussion #2](https://github.com/PolicyEngine/microplex-uk/discussions/2).
- Tracking issue: [#1692](https://github.com/PolicyEngine/policyengine-uk/issues/1692).
- Related: [#1621](https://github.com/PolicyEngine/policyengine-uk/issues/1621) (UK pipeline alignment audit).
- Dataset loader: [`policyengine_uk/simulation.py`](../../../policyengine_uk/simulation.py).
- Default-dataset env var: `POLICYENGINE_UK_DEFAULT_DATASET` (defined in `tax_benefit_system.py`).
