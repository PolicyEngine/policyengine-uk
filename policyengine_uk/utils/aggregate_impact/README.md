# Aggregate impact report

This tool shows what a change does to national numbers. It runs the model on
the certified dataset for two checkouts (a pull request's base and its head)
and compares them. Each side runs every year from 2025-26 to 2031-32 as a full
microsimulation.

The report covers:
- receipts by tax head;
- spending and caseloads by benefit;
- poverty;
- inequality;
- deciles;
- the standard reform costings.

The `Aggregate impact` workflow (`.github/workflows/aggregate-impact.yaml`)
runs it on every pull request and keeps one comment on the PR up to date.

## Data protection

The certified dataset is licensed survey microdata. Only aggregates may be
published: `result.json`, the comment and the comparison summary. `measure`
also writes household-level detail for the decile comparison to
`private/households.npz`. Never upload, attach, commit or share anything
under `private/`, and never put the dataset in a shared cache. The workflow
measures both sides in one job so that this detail stays on the runner, and
`test_aggregate_impact_workflow.py` fails if the workflow could publish it.
Check details give counts and weighted totals, never one household's value.

## Running it

```bash
export HUGGING_FACE_TOKEN=...   # read access to policyengine-uk-data-private
uv run python -m policyengine_uk.utils.aggregate_impact measure --label head \
    --pin policyengine_uk/tests/certified_dataset.yaml --out out/head
# ... the same for a base checkout, into out/base, then:
uv run python -m policyengine_uk.utils.aggregate_impact compare \
    --base out/base --head out/head --markdown comment.md --summary summary.json
```

`measure` downloads the pinned file if it isn't cached, checks its SHA-256, and
writes `result.json` (figures, checks, provenance) and
`private/households.npz` (household detail for the decile comparison). If it crashes, it still writes a
`result.json` recording the crash, so the comparison can report it.

To measure an older checkout with this version of the tool, copy this
directory under another name and run it in that checkout's environment, as CI
does. The tool imports only its own modules and `policyengine_uk`'s public
`Microsimulation`:

```bash
cp -R policyengine_uk/utils/aggregate_impact /tmp/tool/pe_uk_aggregate_impact
cd ../base-checkout && PYTHONPATH=/tmp/tool .venv/bin/python -m pe_uk_aggregate_impact measure ...
```

### Comparing two datasets on one model

A uk-data change is compared the other way round: one model, two datasets.
Measure each built file without a pin, then compare on the data axis:

```bash
uv run python -m policyengine_uk.utils.aggregate_impact measure --label base \
    --dataset-file base/enhanced_frs_2024_25.h5 --dataset-label "main build" --out out/base
uv run python -m policyengine_uk.utils.aggregate_impact measure --label head \
    --dataset-file head/enhanced_frs_2024_25.h5 --dataset-label "PR build" --out out/head
uv run python -m policyengine_uk.utils.aggregate_impact compare --axis data \
    --base out/base --head out/head --markdown comment.md
```

An unpinned file is identified by its SHA-256. The data axis fails unless
both sides ran the same policyengine-uk commit and version, runtime,
partition and metric definitions, so every move is the data's. It does
not match households across the two files: each side's own deciles are
compared instead.

For use from other code (qualification in policyengine.py), see `api.py`:
`compute_budget_metrics(sim, years=...)` returns a long-format report.

## What fails and what is flagged

The comparison **fails** in these cases:
- the head crashes;
- base and head ran on different dataset bytes;
- a figure is not finite;
- the head breaks a check that the base passes.

A check that fails on both sides is reported as pre-existing and does not
fail the job; `--strict` makes it fail. Moves above the thresholds in
`report_spec.yaml` are **flagged** for review, never failed, because intended
policy changes move numbers.

The checks are:
- **closure:** for each model total (`gov_tax`, `household_tax`,
  `pre_budget_change_household_tax`, `gov_spending`, `household_benefits`), the
  components in the model's own list are exactly the partition's heads and
  declared double counts;
- **identities**, checked household by household:
  - the heads and declared double counts add up to each total;
  - `gov_balance` equals `gov_tax` minus `gov_spending`;
  - household net income equals market income plus benefits, less taxes and
    pension contributions;
- **counted once:** each component is raised by £1 per unit, and every head
  of its totals is read household by household. Its own head must rise by
  exactly £1, no other tax head may move, no other benefit may rise (means
  tests may claw the rise back), and the model's own total must move by what
  its heads moved. A head that breaks one of these is measured again with
  every other head held at baseline, and fails only where it still breaks
  it; a response carried by another head (Incapacity Benefit lowers Carer's
  Allowance, which Universal Credit counts as income) is reported as
  mediated. A declared double count must still be contained in its head;
- **signs, bounds and finiteness**, and **determinism:** a rebuilt
  simulation reproduces the baseline exactly;
- **inert heads:** a head that is zero for every unit is a warning, unless the
  partition marks it `zero_at_baseline: expected`;
- **reform responsiveness:** each standard reform must move the variable it
  targets in the stated direction, by at least its stated minimum, in every
  year. Each minimum is a fifth of the reform's smallest yearly effect on the
  certified pair, rounded down to two significant figures (the basis is in
  `standard_reforms.yaml`). After a change that legitimately moves a reform's
  effect, measure the new pair and run
  `python -m policyengine_uk.utils.aggregate_impact calibrate <result.json>...`
  to get the new `smallest_effect` and `minimum`.

## The standard reforms

`standard_reforms.yaml` lists the reforms costed on each side: the eight
reform-cost fixtures, plus a 10% rise in the Universal Credit standard
allowance and a 10% rise in the State Pension. Each says what it must move
(`responds`). A reform that the model ignores, or that moves its target the
wrong way, fails `responsive:<id>` instead of passing as a small number.

A relative reform (`scale`) is built from each side's own baseline: every
listed parameter gets that model year's baseline value times the factor, for
each year of the horizon. Pass `--reforms` to cost a different file, or
`--no-reforms` to cost none.

## The fiscal partition

`policyengine_uk/data/fiscal_partition.yaml` divides each total into heads,
each measured by one variable. Its header defines the fields. Each side of a
comparison reads its own partition, so a change to the model's totals and the
matching change to the partition go in the same pull request.

When you add a component to one of the model's lists, add a head for it, or
the closure check fails. When the model stops counting something twice,
remove its `model_double_counts` entry and give it a head, or the
counted-once check fails as stale.

## Years

Model year 2026 is fiscal year 2026-27. Single-year datasets are projected
through 2032 (`extend_single_year_dataset`, since #2376), so every year of the
report's horizon, 2025-26 to 2031-32, is projected the same way.
