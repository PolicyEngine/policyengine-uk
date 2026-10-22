# VAT grossing to receipts

`vat` and `baseline_vat` compute the statutory liability on each household's
recorded consumption (the standard rate on `full_rate_vat_consumption` plus
the reduced rate on `reduced_rate_vat_consumption`) and divide it by two
factors. This gross amount is calibrated to total VAT receipts. The private
school component is then allocated to `private_school_vat`, as explained
below, so the receipts comparison uses `vat + private_school_vat`:

- `gov.simulation.vat.household_share_of_receipts` (0.7): the share of VAT
  liabilities that falls on household final consumption. HMRC's VAT gap
  estimates put household consumption at around 70% of the VAT total
  theoretical liability; the rest falls on government, charities, VAT-exempt
  businesses and new housing. This is a published quantity and does not depend
  on the dataset.
- `gov.simulation.vat.survey_consumption_coverage` (0.67): the share of
  household VAT liability that the dataset's consumption captures. This
  depends on the dataset's consumption imputation and must be re-derived when
  the default dataset changes.

The incidence assumption is that every pound of receipts, including VAT that
government, charities and exempt businesses pay on their inputs, is passed on
to households in proportion to their own VAT-liable spending.

These two factors replace `gov.simulation.microdata_vat_coverage`, a single
undated 0.38 added in January 2023 against an older LCFS-based consumption
imputation, with no derivation recorded. Its product with today's datasets put
2024-25 VAT 24% above OBR receipts on Microcosm UK 2024-25 and 71% above on
Enhanced FRS 2024-25 (policyengine-uk-data 1.56.16).

`gov.simulation.microdata_vat_coverage` is kept as a deprecated parameter so
that existing reforms to it still work. Its value is now the product of the two
factors (0.469). If a reform sets it to any other value, `vat` and
`baseline_vat` use that value in place of the two factors
(`policyengine_uk/utils/vat.py`); otherwise they use the two factors. New
reforms should change the two factors instead.

## Which datasets the factor applies to

The survey coverage of 0.67 is calibrated to one dataset: the certified
Microcosm UK 2024-25 national release. It does not carry over to other
datasets, because their consumption imputations capture a different share of
household VAT. On Enhanced FRS 2024-25 it puts VAT 35% to 44% above receipts,
depending on the release and year (see the tables below). Re-derive the coverage, with
the calculation below, whenever the dataset it should match changes.

## Derivation (October 2026)

### Inputs

| Input | Value | Source |
|---|---|---|
| Microcosm UK 2024-25 national release | `microcosm_uk_2024_25.h5`, Hugging Face `policyengine/populace-uk-private`, tag `microcosm-uk-2024-25-national-20261002T230158Z-5c6b3f68` (revision `f9d1922c`), SHA-256 `aa31bdf67c977927ea2b325567d1cf7a79d94381239bc79918a0a0fc9c9588af` | Private repository |
| Enhanced FRS 2024-25 | `enhanced_frs_2024_25.h5`, Hugging Face `policyengine/policyengine-uk-data-private`, policyengine-uk-data 1.56.16 (revision `a9e52499`, SHA-256 `e433e532b17bd8ce76030156285816e33d44e93edabd2204adbef71d19a68712`) and 1.58.0 (revision `47bbb58d`, SHA-256 `5ba399ea5ab9a6c7d4e9aaf6c623080beb34d9ad5f330f6244dbad72b8d960b6`) | Private repository |
| VAT receipts | £170.994bn (2024-25 outturn), £180.169bn (2025-26), £187.704bn (2026-27) | OBR, Economic and fiscal outlook March 2026, detailed forecast tables, receipts, table 3.8, cash-basis VAT |
| Household share of VAT liabilities | 0.7 | HMRC VAT gap estimates (around 70% of the VAT total theoretical liability); `household_share_of_receipts` |
| Ready reckoner | £8.8bn for one point on the standard rate, 2026-27 | HMRC, Direct effects of illustrative tax changes (June 2025) |
| Statutory rates | 20% standard, 5% reduced | `gov.hmrc.vat` |

Model year 2024 is the 2024-25 fiscal year. All dataset totals are weighted
sums from `Microsimulation`, computed with policyengine-uk at this branch and
policyengine-core 3.33.2.

### Formula

```
pre-scaling VAT = 0.20 x sum(full_rate_vat_consumption)
                + 0.05 x sum(reduced_rate_vat_consumption)
product         = pre-scaling VAT / OBR VAT receipts      (same year)
survey coverage = product / household share (0.7)
```

Dividing each household's statutory VAT by the product gives the gross
amount. At current law, total `vat + private_school_vat` equals this amount,
and equals receipts when the product matches the dataset.

### Results

| Dataset | Year | Standard-rated base | Reduced-rated base | Pre-scaling VAT | Receipts | Product | Survey coverage |
|---|---|---|---|---|---|---|---|
| Microcosm UK 2024-25 (`f9d1922c`) | 2024-25 | £396.15bn | £25.02bn | £80.48bn | £171.0bn | 0.471 | 0.672 |
| Microcosm UK 2024-25 (`f9d1922c`) | 2025-26 | £412.57bn | £26.06bn | £83.82bn | £180.2bn | 0.465 | 0.665 |
| Microcosm UK 2024-25 (`f9d1922c`) | 2026-27 | £423.66bn | £26.76bn | £86.07bn | £187.7bn | 0.459 | 0.655 |
| Enhanced FRS 2024-25, uk-data 1.56.16 | 2024-25 | £546.96bn | £32.21bn | £111.00bn | £171.0bn | 0.649 | 0.927 |
| Enhanced FRS 2024-25, uk-data 1.56.16 | 2025-26 | £569.63bn | £33.55bn | £115.60bn | £180.2bn | 0.642 | 0.917 |
| Enhanced FRS 2024-25, uk-data 1.56.16 | 2026-27 | £584.95bn | £34.45bn | £118.71bn | £187.7bn | 0.632 | 0.904 |
| Enhanced FRS 2024-25, uk-data 1.58.0 | 2024-25 | £570.29bn | £33.17bn | £115.72bn | £171.0bn | 0.677 | 0.967 |
| Enhanced FRS 2024-25, uk-data 1.58.0 | 2025-26 | £593.92bn | £34.54bn | £120.51bn | £180.2bn | 0.669 | 0.956 |
| Enhanced FRS 2024-25, uk-data 1.58.0 | 2026-27 | £609.89bn | £35.47bn | £123.75bn | £187.7bn | 0.659 | 0.942 |

The parameter takes the Microcosm 2024-25 value, 0.67 (product 0.469), the
latest outturn year.

With that product, total current-law `vat + private_school_vat` against receipts is:

| Dataset | 2024-25 | 2025-26 | 2026-27 |
|---|---|---|---|
| Microcosm UK 2024-25 (`f9d1922c`) | £171.6bn (+0.4%) | £178.7bn (-0.8%) | £183.5bn (-2.2%) |
| Enhanced FRS 2024-25, uk-data 1.56.16 | £236.7bn (+38.4%) | £246.5bn (+36.8%) | £253.1bn (+34.8%) |
| Enhanced FRS 2024-25, uk-data 1.58.0 | £246.7bn (+44.3%) | £257.0bn (+42.6%) | £263.9bn (+40.6%) |

### Bound

Total VAT depends only on the product, so the household share being a
rounded "around 70%" changes how the product is split between the two factors,
not the totals. On Microcosm the product is bounded by:

- the receipts route across 2024-25 to 2026-27: 0.459 to 0.471 (coverage 0.655
  to 0.672);
- the ready reckoner, which does not use the level of receipts: one point on
  the standard rate raises £4.24bn before scaling in 2026-27 (1% of
  £423.66bn), so matching HMRC's £8.8bn needs a product of 0.481 (coverage
  0.688).

So on Microcosm the product lies between 0.459 and 0.481, and the coverage
between 0.655 and 0.688 at a household share of 0.7. The value used, 0.469
(0.67), sits inside that range, and the totals it gives are within 2.2% of
receipts from 2024-25 to 2026-27. The implied product moves by less than 3%
over those years, so the factors are not dated by year.

### Reproducing

The two datasets are in private Hugging Face repositories. Anyone with
PolicyEngine access can rerun the calculation; anyone else can check the
arithmetic from the published aggregates in the results table.

```python
from huggingface_hub import hf_hub_download
from policyengine_uk import Microsimulation

path = hf_hub_download(
    "policyengine/populace-uk-private",
    "microcosm_uk_2024_25.h5",
    repo_type="dataset",
    revision="f9d1922cddab6b54a0dd37794a9bac74e3780c88",
)
sim = Microsimulation(dataset=path)
# OBR March 2026 EFO, table 3.8, cash-basis VAT receipts
receipts = {2024: 170.994e9, 2025: 180.169e9, 2026: 187.704e9}
for year, obr in receipts.items():
    p = sim.tax_benefit_system.parameters(f"{year}-01-01").gov.hmrc.vat
    full = sim.calculate("full_rate_vat_consumption", year).sum()
    reduced = sim.calculate("reduced_rate_vat_consumption", year).sum()
    raw = full * p.standard_rate + reduced * p.reduced_rate
    print(year, raw / 1e9, raw / obr, raw / obr / 0.7)
```

For Enhanced FRS, download `enhanced_frs_2024_25.h5` from the model repository
`policyengine/policyengine-uk-data-private` at the release tag (for example
`revision="1.58.0"`).

## Private school VAT: splitting the existing receipts total

The OBR VAT total already includes VAT on private school fees. HMRC's
[VAT-only costing](https://www.gov.uk/government/publications/vat-on-private-school-fees/applying-vat-to-private-school-fees)
is £460m in 2024-25, £1,505m in 2025-26 and £1,560m in 2026-27. Adding a
separate school VAT head to the gross amount above would count that receipt
twice. The model instead separates the school component from the existing
receipts allocation, keeping the survey coverage at 0.67.

For each household, let `G` be the gross VAT amount above, `P0` be
`baseline_private_school_vat`, `P` be `private_school_vat`, `r0` be the
baseline standard rate and `r` be the current standard rate. The allocation
is:

```text
school component already in gross VAT = P0 * r / r0
vat                                  = G - P0 * r / r0
baseline_vat                         = G0 - P0
combined VAT                         = vat + P
                                     = G + P - P0 * r / r0
```

At current law, `r = r0` and `P = P0`, so combined VAT is exactly `G` for
every household, year and dataset. The same identity holds after weighting
and aggregation. It also holds when only the standard rate changes: both
the allocated component and the explicit school charge move with that
rate. Subtracting a fixed `P0` from current `vat` would count that rate
change twice. Restoring the school exemption leaves the allocation in
place and sets `P` to zero, reducing combined VAT by the school charge.

Both school measures use this simulation's attendance, fees and effective
VAT basis, with baseline policy held fixed for `P0`. Consequently, changes
to those assumptions alone preserve the current-law receipts total. The
official £1,560m costing is a useful external comparison, but subtracting it
instead of the model's own school component would leave a residual equal
to the difference between the two. It would also require a dataset-specific
allocation of that national amount. No new coverage factor is needed for
this accounting split.

The receipts check therefore retains the original calibration's accuracy.
Using the rounded 2024-25 Microcosm inputs above,
`80.48 / (0.67 * 0.7) = £171.599bn`, compared with OBR's £170.994bn: about
0.35% above receipts. The table's 2025-26 and 2026-27 comparisons also stay
unchanged. This split prevents an additional school VAT overstatement; the
existing differences from receipts, including Enhanced FRS's larger
overstatement, still require dataset-specific calibration. Aggregate impact
CI compares the combined VAT report group against the PR's base.

Two limits matter when interpreting the split. Model year 2024 represents
2024-25 but reads annual policy before the January 2025 commencement, so
`P0` is zero for that year. The £460m part-year receipt remains in general
VAT; this change does not model its separate timing. Also, general `vat`
can be negative when a household has imputed or entered school attendance
and too little recorded consumption to cover the allocated school
component. It is a receipt-allocation residual. Clipping it to zero would
break the receipts identity; the combined current-law amount still equals
the original gross amount.

## Interaction with an explicit energy VAT base

A domestic fuel and power VAT base built from `electricity_consumption` and
`gas_consumption` (PolicyEngine/policyengine-uk#2166) changes what the survey
coverage applies to. If those energy inputs are already calibrated to an
aggregate, they should not be divided by the survey coverage again, and the
reconciled energy part of `reduced_rate_vat_consumption` should come out of the
base used to derive it.
