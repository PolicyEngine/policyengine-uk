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

## Running it

```bash
export HUGGING_FACE_TOKEN=...   # read access to policyengine-uk-data-private
uv run python -m policyengine_uk.utils.aggregate_impact measure --label head \
    --pin policyengine_uk/tests/certified_dataset.yaml \
    --reforms policyengine_uk/tests/microsimulation/reforms_config.yaml \
    --out out/head
# ... the same for a base checkout, into out/base, then:
uv run python -m policyengine_uk.utils.aggregate_impact compare \
    --base out/base --head out/head --markdown comment.md --summary summary.json
```

`measure` downloads the pinned file if it isn't cached, checks its SHA-256, and
writes `result.json` (figures, checks, provenance) and `households.npz`
(household detail for the decile comparison). If it crashes, it still writes a
`result.json` recording the crash, so the comparison can report it.

To measure an older checkout with this version of the tool, copy this
directory under another name and run it in that checkout's environment, as CI
does. The tool imports only its own modules and `policyengine_uk`'s public
`Microsimulation`:

```bash
cp -R policyengine_uk/utils/aggregate_impact /tmp/tool/pe_uk_aggregate_impact
cd ../base-checkout && PYTHONPATH=/tmp/tool .venv/bin/python -m pe_uk_aggregate_impact measure ...
```

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
- **counted once:** each component is raised by £1 per unit. Each tax total it
  is in must rise by exactly £1 per unit, and each spending total by at most
  £1, because means tests can claw the rise back but nothing should add to
  it. A declared double count must still be contained in its head;
- **signs, bounds and finiteness**, and **determinism:** a rebuilt
  simulation reproduces the baseline exactly;
- **inert heads:** a head that is zero for every unit is a warning, unless the
  partition marks it `zero_at_baseline: expected`.

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

Model year 2026 is fiscal year 2026-27. The dataset is extended explicitly to
2030 (`extend_single_year_dataset`). Values for 2031-32 come from
policyengine-core instead:
- inputs with an `uprating` index are uprated from their 2030 values;
- other inputs are carried over unchanged.

So treat 2031-32 figures as provisional.
