# Reform impacts dashboard (planned)

```{note}
**Planning page.** Tracks
[#806](https://github.com/PolicyEngine/policyengine-uk/issues/806),
which asks for a dashboard tracking the budgetary impact of
high-importance reforms over time and across model versions.
The repo already has the **fixtures**, and each one now records its
earlier values with the model and data that produced them; what's
missing is a published view onto them. Updated October 2026: still not
built, and the planned dataset move to Microcosm UK (below) makes it more
useful.
```

## What exists today

[`policyengine_uk/tests/microsimulation/reforms_config.yaml`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/tests/microsimulation/reforms_config.yaml)
names the dataset the fixtures were measured on and lists the canonical
reform-impact regression fixtures. Each fixture keeps its earlier values
under `receipts`, with the model and data that produced each. Abridged,
at policyengine-uk 2.148.2:

```yaml
dataset:
  data_version: 1.58.1
  path: enhanced_frs_2024_25.h5
  revision: 2526edbbb687a3b54dbb11272e5389e4b62d2ac2
  sha256: 056e80fd8e9151d78f432a25cde863340baee81304c6216a37fb575ce8563784
reforms:
- name: Raise basic rate by 1pp
  expected_impact: 7.1
  parameters:
    gov.hmrc.income_tax.rates.uk[0].rate: 0.21
  receipts:
  - impact: 7.8
    data: enhanced_frs_2022_23, unpinned (latest at the time)
    model: 2.34.5 (a1832dc77, #1205, 2025-07-11)
  # ... four more receipts ...
  - impact: 7.115
    data: 1.58.1 enhanced_frs_2024_25
    model: 2.135.7 (merged 7717438bf, main 7ad002f54, 2026-10-18)
# ...
- name: Reduce Universal Credit taper rate to 20%
  expected_impact: -22.0
  tolerance: 3.0
  parameters:
    gov.dwp.universal_credit.means_test.reduction_rate: 0.2
  receipts:
  # ...
```

Each fixture is run by
[`policyengine_uk/tests/microsimulation/test_reform_impacts.py`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/tests/microsimulation/test_reform_impacts.py),
which compares the change in `gov_balance` in 2029 with
`expected_impact` (£bn), within `tolerance` (default £1bn). The tests
are marked `microsimulation`, so they run in CI's test suite only when a
dataset is available: `policyengine_uk/tests/conftest.py` points
`POLICYENGINE_UK_DEFAULT_DATASET` at the certified dataset pinned in
`policyengine_uk/tests/certified_dataset.yaml` when a Hugging Face token
is set. That dataset is the Enhanced FRS 2024-25
(`enhanced_frs_2024_25.h5` from policyengine-uk-data 1.58.1), pinned by
Hugging Face commit and checked against its SHA-256. The suite requires
that data in the merge queue and on main, and skips these tests on pull
requests without credentials. So CI already catches *unintended* impact
changes before they reach main. But the test itself is only pass or fail.
The `Aggregate impact` workflow
(`.github/workflows/aggregate-impact.yaml`) also costs these reforms on
each pull request's base and head for 2025-26 to 2031-32 and posts the
comparison as a pull request comment, but nothing keeps those results
once the pull request is done. When a change is intended, someone reruns
[`update_reform_impacts.py`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/tests/microsimulation/update_reform_impacts.py),
which overwrites `expected_impact`. The earlier values survive only
because each fixture also keeps a `receipts` list: the script does not
add to it, but a test requires the latest receipt to be on the pinned
dataset and to match `expected_impact`. The fixtures are regression
values taken from the model's own output, not external costings (the
file says so at the top).

What's missing is a **time series** that keeps itself: the receipts hold
only the values someone chose to record, for 2029, and the
aggregate-impact comments aren't stored. The plan is the same eight
reforms run on every commit or version, plotted against a published
external costing where one exists (for the tax-rate changes, HMRC's
[ready reckoner](https://www.gov.uk/government/statistics/direct-effects-of-illustrative-tax-changes)),
with annotations for the relevant infrastructure changes (model
versions, dataset refreshes, EFO updates).

## Proposed shape

### Storage

Each scheduled run writes a row per fixture to a CSV / Parquet on
HuggingFace Hub or a small Postgres instance:

```
timestamp, policyengine_uk_version, policyengine_uk_data_version,
dataset_url, reform_name, expected_impact, observed_impact, gap
```

The table is append-only, with no overwrites, so the history survives.

### Computation

A new entry point under `tests/microsimulation/` (or, better, a
GitHub Actions workflow that doesn't run inside the test suite)
walks `reforms_config.yaml`, runs each reform, and writes a row
per fixture. Schedule: weekly + on every release tag.
(`python -m policyengine_uk.utils.aggregate_impact measure` already does
the costing, for the eight fixtures and two more reforms; the new part is
running it on a schedule and keeping the results.)

### Publication

Three publication paths, in order of effort:

1. **Static page in the docs site**: the simplest. Convert the CSV
   to a Plotly chart (as `validation/validation.ipynb` does) and render
   it under `docs/book/validation/`. A notebook must be added to
   `myst.yml` by name, since only Markdown pages are picked up by
   folder. Updates when the docs site rebuilds.
2. **Living JSON endpoint**: push the latest aggregate JSON to a
   stable URL (a HuggingFace dataset or a GitHub Pages artefact) so the
   policyengine.org app can render it without needing the docs build.
3. **policyengine.org dashboard tile**: a tile on the marketing site
   that shows the latest impact alongside the OBR/RF benchmark. Most
   work; right answer once the static page proves the data is stable.

### What to put on the dashboard

For each reform:

- **Latest observed impact** (£bn, current model).
- **Published external benchmark** where one exists, with its
  publication date: HMRC's ready reckoner (*Direct effects of
  illustrative tax changes*) for the income tax, National Insurance and
  VAT changes, and OBR or Resolution Foundation costings (such as RF's
  *No half measures* on the two-child limit) for the policies they
  cover. Any published figure must follow the aggregate-impact privacy
  rules (`policyengine_uk/utils/aggregate_impact/privacy.py`).
- **Time series** of observed impact across the last N model releases.
- **Annotations** for each known regime shift: EFO release, dataset
  refresh, methodology PR. The reforms_config history is the natural
  source of "what changed" annotations.

## Initial reform list

Use the existing `reforms_config.yaml` entries as the v1 dashboard
content:

1. Raise basic rate by 1pp.
2. Raise the higher rate to 42% (the fixture's name says "by 1pp", but
   the rate is 40%, so the rise is 2pp).
3. Raise the personal allowance to £13,000 (the fixture's name says
   "by ~800GBP/year", but the allowance is frozen at £12,570 to
   2030-31, so in 2029 the rise is £430).
4. Set the child benefit rate for each additional child to £25 a week.
5. Reduce Universal Credit taper to 20%.
6. Raise Class 1 main employee NI rate to 10%.
7. Raise VAT standard rate by 2pp.
8. Raise additional rate by 3pp.

These cover income tax (four fixtures), National Insurance and VAT,
plus two benefit parameters: the Child Benefit rate for additional
children and the Universal Credit taper.

Add to v2 over time as published OBR / RF reforms become available
benchmarks:

- Reinstate the two-child limit. The baseline removes it from 6 April
  2026, and [child-poverty-tcl.md](child-poverty-tcl.md) compares its
  removal with the DWP, Budget 2025 and Resolution Foundation estimates.
- Freeze the Personal Allowance for an additional year (to 2031-32, so
  it needs a later reference year than 2029).
- 1pp employer NI change.

## Why now

The UK data pipeline is moving from the Enhanced FRS to
[Microcosm UK](https://github.com/PolicyEngine/microcosm), while the
fixtures still run on the Enhanced FRS (2024-25, from
policyengine-uk-data 1.58.1). Moving the
fixtures' dataset will shift every expected impact at once, and model
changes to VAT, fuel duty and other bases are landing at the same time.
A history that records the dataset alongside each value is the easiest
way to show which change moved which number.

## What this doesn't replace

This is a **regression-tracking** dashboard, not a forecast. The
numbers it plots are PolicyEngine UK's reading of a reform under
current model + data + EFO assumptions; they will move when any of
those move, by design. The whole point of plotting the time series is
to make those movements legible rather than hidden.

For comparison with external nowcasters (RF, IFS, OBR scoring), the
relevant pages are:

- [nowcasting-comparison.md](../assumptions/nowcasting-comparison.md) (PolicyEngine vs RF).
- [rf-nowcasting-methodology.md](../assumptions/rf-nowcasting-methodology.md) (RF methodology detail).
- [child-poverty-tcl.md](child-poverty-tcl.md) (the child-poverty impact and cost of removing the two-child limit, against DWP, Budget 2025 and Resolution Foundation estimates).

## Open questions

- Storage substrate: HuggingFace dataset CSV vs a small managed
  database. CSV is simplest; database lets the policyengine.org app
  query directly.
- Scheduling: every commit to main, every weekly tag, or both?
  Recommend weekly + on tag, since per-commit runs cost
  microsim time without proportional information gain.
- Should the dashboard include reform variants from the policyengine
  blog series, or stick to the parametric fixtures? Recommend
  parametric fixtures only for v1 to keep maintenance burden low.

## References

- Issue: [#806](https://github.com/PolicyEngine/policyengine-uk/issues/806).
- Existing fixture list: [`reforms_config.yaml`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/tests/microsimulation/reforms_config.yaml).
- Existing regression runner: [`test_reform_impacts.py`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/tests/microsimulation/test_reform_impacts.py).
- Script that rewrites the expected values: [`update_reform_impacts.py`](https://github.com/PolicyEngine/policyengine-uk/blob/main/policyengine_uk/tests/microsimulation/update_reform_impacts.py).
- Per-pull-request costings: [`.github/workflows/aggregate-impact.yaml`](https://github.com/PolicyEngine/policyengine-uk/blob/main/.github/workflows/aggregate-impact.yaml) and [`policyengine_uk/utils/aggregate_impact/`](https://github.com/PolicyEngine/policyengine-uk/tree/main/policyengine_uk/utils/aggregate_impact).
