# Reform impacts dashboard (planned)

```{note}
**Planning page.** Tracks
[#806](https://github.com/PolicyEngine/policyengine-uk/issues/806),
which asks for a dashboard tracking the budgetary impact of
high-importance reforms over time and across model / data versions.
The repo already has the **fixtures** — what's missing is a published
view onto them. Updated October 2026: still not built; the dataset move
to Microcosm UK (below) makes it more useful.
```

## What exists today

[`policyengine_uk/tests/microsimulation/reforms_config.yaml`](../../../policyengine_uk/tests/microsimulation/reforms_config.yaml)
is a list of canonical reform-impact regression fixtures with the
shape:

```yaml
- name: Raise basic rate by 1pp
  expected_impact: 7.8     # £bn fiscal impact at the reference year
  parameters:
    gov.hmrc.income_tax.rates.uk[0].rate: 0.21
- name: Reduce Universal Credit taper rate to 20%
  expected_impact: -18.1
  tolerance: 3.0
  parameters:
    gov.dwp.universal_credit.means_test.reduction_rate: 0.2
```

Each fixture is run by
[`tests/microsimulation/test_reform_impacts.py`](../../../policyengine_uk/tests/microsimulation/test_reform_impacts.py),
which compares the change in `gov_balance` in 2029 with
`expected_impact` (£bn), within `tolerance` (default £1bn). It runs in
CI's Test job on every PR, on the dataset CI is configured with, so CI
already catches *unintended* impact changes. But the signal is only
pass or fail, and when a change is intended, someone reruns
[`update_reform_impacts.py`](../../../policyengine_uk/tests/microsimulation/update_reform_impacts.py)
and the old value is overwritten. The fixtures are regression values
taken from the model's own output, not external costings (the file says
so at the top).

What's missing is a **time series**: the same eight reforms run on
every commit / version, plotted against the published OBR/RF
benchmark for the same reform, with annotations for the relevant
infrastructure changes (model versions, dataset refreshes, EFO
updates).

## Proposed shape

### Storage

Each scheduled run writes a row per fixture to a CSV / Parquet on
HuggingFace Hub or a small Postgres instance:

```
timestamp, policyengine_uk_version, policyengine_uk_data_version,
dataset_url, reform_name, expected_impact, observed_impact, gap
```

Append-only — no overwrites — so the history survives.

### Computation

A new entry point under `tests/microsimulation/` (or, better, a
GitHub Actions workflow that doesn't run inside the test suite)
walks `reforms_config.yaml`, runs each reform, and writes a row
per fixture. Schedule: weekly + on every release tag.

### Publication

Three publication paths, in order of effort:

1. **Static page in the docs site** — the simplest. Convert the CSV
   to a Plotly chart (matching the existing `validation/*.ipynb`
   pattern) and render it under `docs/book/validation/`. Updates
   when the docs site rebuilds.
2. **Living JSON endpoint** — push the latest aggregate JSON to a
   stable URL (HuggingFace dataset or a `gh-pages` artefact) so the
   policyengine.org app can render it without needing the docs build.
3. **policyengine.org dashboard tile** — a tile on the marketing site
   that shows the latest impact alongside the OBR/RF benchmark. Most
   work; right answer once the static page proves the data is stable.

### What to put on the dashboard

For each reform:

- **Latest observed impact** (£bn, current model).
- **Published external benchmark** (OBR EFO costing where one
  exists; RF *No half measures*-style costing as a comparator). Annotate
  the publication date.
- **Time series** of observed impact across the last N model releases.
- **Annotations** for each known regime shift: EFO release, dataset
  refresh, methodology PR. The reforms_config history is the natural
  source of "what changed" annotations.

## Initial reform list

Use the existing `reforms_config.yaml` entries as the v1 dashboard
content:

1. Raise basic rate by 1pp.
2. Raise higher rate by 1pp.
3. Raise personal allowance by ~£800/year.
4. Raise child benefit by £25/week per additional child.
5. Reduce Universal Credit taper to 20%.
6. Raise Class 1 main employee NI rate to 10%.
7. Raise VAT standard rate by 2pp.
8. Raise additional rate by 3pp.

These cover three of the four big revenue heads (income tax, NI, VAT)
plus a UC parameter that matters disproportionately for distributional
analysis.

Add to v2 over time as published OBR / RF reforms become available
benchmarks:

- Remove the two-child limit (an external comparison is drafted in
  [#1724](https://github.com/PolicyEngine/policyengine-uk/pull/1724)).
- Freeze the Personal Allowance for an additional year.
- 1pp employer NI change.

## Why now

The UK data pipeline is moving from the Enhanced FRS to
[Microcosm UK](https://github.com/PolicyEngine/microcosm), whose first
certified national release was published on 4 October 2026. Moving the
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
- [#1724](https://github.com/PolicyEngine/policyengine-uk/pull/1724) (child poverty against OBR and Resolution Foundation benchmarks, in review).

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
- Existing fixture list: [`reforms_config.yaml`](../../../policyengine_uk/tests/microsimulation/reforms_config.yaml).
- Existing regression runner: [`test_reform_impacts.py`](../../../policyengine_uk/tests/microsimulation/test_reform_impacts.py).
- Script that rewrites the expected values: [`update_reform_impacts.py`](../../../policyengine_uk/tests/microsimulation/update_reform_impacts.py).
