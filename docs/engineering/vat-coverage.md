# VAT grossing to receipts

`vat` and `baseline_vat` compute the statutory liability on each household's
recorded consumption (the standard rate on `full_rate_vat_consumption` plus
the reduced rate on `reduced_rate_vat_consumption`) and divide it by two
factors, so that total VAT matches receipts:

- `gov.simulation.vat.household_share_of_receipts` (0.7): the share of VAT
  liabilities that falls on household final consumption. HMRC's VAT gap
  estimates put household consumption at around 70% of the VAT total
  theoretical liability; the rest falls on government, charities, VAT-exempt
  businesses and new housing. This is a published quantity and does not depend
  on the dataset.
- `gov.simulation.vat.survey_consumption_coverage` (0.74): the share of
  household VAT liability that the dataset's consumption captures. This
  depends on the dataset's consumption imputation and must be re-derived when
  the default dataset changes.

The incidence assumption is that every pound of receipts, including VAT that
government, charities and exempt businesses pay on their inputs, is passed on
to households in proportion to their own VAT-liable spending.

These two factors replace `gov.simulation.microdata_vat_coverage`, a single
undated 0.38 added in January 2023 against an older LCFS-based consumption
imputation, with no derivation recorded.

`gov.simulation.microdata_vat_coverage` is kept as a deprecated parameter so
that existing reforms to it still work. Its value is now the product of the two
factors (0.518). If a reform sets it to any other value, `vat` and
`baseline_vat` use that value in place of the two factors
(`policyengine_uk/utils/vat.py`); otherwise they use the two factors. New
reforms should change the two factors instead.

## Which datasets the factor applies to

The survey coverage of 0.74 is calibrated to one dataset: the certified
Microcosm UK 2024-25 national release `a133f37a`. It does not carry over to
other datasets, because their consumption imputations capture a different
share of household VAT: on Enhanced FRS 2024-25 its implied coverage is
0.90 to 0.97 (see the tables below). Re-derive the coverage, with the calculation below, whenever the dataset it
should match changes.

## Derivation (24 October 2026)

The first derivation (#2187, 0.67) used the Microcosm release `f9d1922c`.
That release was replaced by the `6cba5d71` and `a133f37a` cuts, which record
about 10% more standard-rated consumption. With 0.67, total `vat` on
`a133f37a` ran 7.5% to 10.3% above receipts in 2024-25 to 2026-27. On
`6cba5d71` (revision `bb225848`), a reform run that raises the standard rate
from 20% to 21% changed total `vat` by £9.94bn in 2026-27 (£9.68bn in
2025-26), 12.9% above HMRC's ready reckoner. That is the reform run minus the
baseline run, with policyengine-uk 2.135.7 and again with 2.152.6, which give
the same figure; `gov_balance` changed by the same amount. This derivation
repeats the same calculation on `a133f37a`
(PolicyEngine/policyengine-uk#2633).

### Inputs

| Input | Value | Source |
|---|---|---|
| Microcosm UK 2024-25 national release | `microcosm_uk_2024_25.h5`, Hugging Face `policyengine/populace-uk-private`, tag `microcosm-uk-2024-25-national-20261023T075039Z-a133f37a` (revision `c3a751d9`), SHA-256 `64f83900ca3a1242fb017585234844ce89f743d32e41cd2b6558057777f914aa` | Private repository |
| Microcosm UK 2024-25 national release, cross-check | tag `microcosm-uk-2024-25-national-20261019T083323Z-6cba5d71` (revision `bb225848`), SHA-256 `810ba980005a8b907cb51464279fa5e0125464b7af9a4871b7f6744c30951ece` | Private repository |
| Microcosm UK 2024-25 national release, first derivation | tag `microcosm-uk-2024-25-national-20261002T230158Z-5c6b3f68` (revision `f9d1922c`), SHA-256 `aa31bdf67c977927ea2b325567d1cf7a79d94381239bc79918a0a0fc9c9588af` | Private repository |
| Enhanced FRS 2024-25 | `enhanced_frs_2024_25.h5`, Hugging Face `policyengine/policyengine-uk-data-private`, policyengine-uk-data 1.56.16 (revision `a9e52499`, SHA-256 `e433e532b17bd8ce76030156285816e33d44e93edabd2204adbef71d19a68712`) and 1.58.0 (revision `47bbb58d`, SHA-256 `5ba399ea5ab9a6c7d4e9aaf6c623080beb34d9ad5f330f6244dbad72b8d960b6`) | Private repository |
| VAT receipts | £170.994bn (2024-25 outturn), £180.169bn (2025-26), £187.704bn (2026-27) | OBR, Economic and fiscal outlook March 2026, detailed forecast tables, receipts, table 3.8, cash-basis VAT |
| Household share of VAT liabilities | 0.7 | HMRC VAT gap estimates (around 70% of the VAT total theoretical liability); `household_share_of_receipts` |
| Ready reckoner | £8.8bn for one point on the standard rate, 2026-27 | HMRC, Direct effects of illustrative tax changes (June 2025) |
| Statutory rates | 20% standard, 5% reduced | `gov.hmrc.vat` |

Model year 2024 is the 2024-25 fiscal year. All dataset totals are weighted
sums from `Microsimulation`. The `a133f37a` rows were computed with
policyengine-uk 2.152.7 (this branch's base, main `c0252415a`) and
policyengine-core 3.33.2, and again with policyengine-uk 2.147.2 and
policyengine-core 3.33.3, which give the same totals. The `6cba5d71` rows were
computed with policyengine-uk 2.147.2 and policyengine-core 3.33.3. The other
rows come from the first derivation.

### Formula

```
pre-scaling VAT = 0.20 x sum(full_rate_vat_consumption)
                + 0.05 x sum(reduced_rate_vat_consumption)
product         = pre-scaling VAT / OBR VAT receipts      (same year)
survey coverage = product / household share (0.7)
```

`vat` divides each household's statutory VAT by the product, so total `vat`
equals receipts when the product matches the dataset.

### Results

| Dataset | Year | Standard-rated base | Reduced-rated base | Pre-scaling VAT | Receipts | Product | Survey coverage |
|---|---|---|---|---|---|---|---|
| Microcosm UK 2024-25 (`a133f37a`) | 2024-25 | £435.60bn | £26.76bn | £88.46bn | £171.0bn | 0.517 | 0.739 |
| Microcosm UK 2024-25 (`a133f37a`) | 2025-26 | £453.65bn | £27.87bn | £92.12bn | £180.2bn | 0.511 | 0.730 |
| Microcosm UK 2024-25 (`a133f37a`) | 2026-27 | £465.85bn | £28.62bn | £94.60bn | £187.7bn | 0.504 | 0.720 |
| Microcosm UK 2024-25 (`6cba5d71`) | 2024-25 | | | £88.51bn | £171.0bn | 0.518 | 0.739 |
| Microcosm UK 2024-25 (`6cba5d71`) | 2025-26 | | | £92.18bn | £180.2bn | 0.512 | 0.731 |
| Microcosm UK 2024-25 (`6cba5d71`) | 2026-27 | | | £94.66bn | £187.7bn | 0.504 | 0.720 |
| Microcosm UK 2024-25 (`f9d1922c`) | 2024-25 | £396.15bn | £25.02bn | £80.48bn | £171.0bn | 0.471 | 0.672 |
| Microcosm UK 2024-25 (`f9d1922c`) | 2025-26 | £412.57bn | £26.06bn | £83.82bn | £180.2bn | 0.465 | 0.665 |
| Microcosm UK 2024-25 (`f9d1922c`) | 2026-27 | £423.66bn | £26.76bn | £86.07bn | £187.7bn | 0.459 | 0.655 |
| Enhanced FRS 2024-25, uk-data 1.56.16 | 2024-25 | £546.96bn | £32.21bn | £111.00bn | £171.0bn | 0.649 | 0.927 |
| Enhanced FRS 2024-25, uk-data 1.56.16 | 2025-26 | £569.63bn | £33.55bn | £115.60bn | £180.2bn | 0.642 | 0.917 |
| Enhanced FRS 2024-25, uk-data 1.56.16 | 2026-27 | £584.95bn | £34.45bn | £118.71bn | £187.7bn | 0.632 | 0.904 |
| Enhanced FRS 2024-25, uk-data 1.58.0 | 2024-25 | £570.29bn | £33.17bn | £115.72bn | £171.0bn | 0.677 | 0.967 |
| Enhanced FRS 2024-25, uk-data 1.58.0 | 2025-26 | £593.92bn | £34.54bn | £120.51bn | £180.2bn | 0.669 | 0.956 |
| Enhanced FRS 2024-25, uk-data 1.58.0 | 2026-27 | £609.89bn | £35.47bn | £123.75bn | £187.7bn | 0.659 | 0.942 |

The parameter takes the `a133f37a` value for the latest outturn year, 0.739,
rounded to 0.74 (product 0.518).

With that product, total `vat` against receipts, from runs at this branch:

| Dataset | 2024-25 | 2025-26 | 2026-27 |
|---|---|---|---|
| Microcosm UK 2024-25 (`a133f37a`) | PENDING | PENDING | PENDING |
| Enhanced FRS 2024-25, uk-data 1.58.1 | PENDING | PENDING | PENDING |

### Bound

Total VAT depends only on the product, so the household share being a
rounded "around 70%" changes how the product is split between the two factors,
not the totals. On `a133f37a` the product is bounded by:

- the receipts route across 2024-25 to 2026-27: 0.504 to 0.517 (coverage 0.720
  to 0.739);
- the ready reckoner, which does not use the level of receipts: one point on
  the standard rate raises £4.66bn before scaling in 2026-27 (1% of
  £465.85bn), so matching HMRC's £8.8bn needs a product of 0.529 (coverage
  0.756). With the product used, a reform run of one point costs PENDING.

So on `a133f37a` the product lies between 0.504 and 0.529, and the coverage
between 0.720 and 0.756 at a household share of 0.7. The value used, 0.518
(0.74), sits inside that range. The implied product moves by less than 3%
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
    revision="c3a751d911ac82e482d298dda0b6f2c949f4ed4d",  # tag ...-a133f37a
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

## Interaction with an explicit energy VAT base

A domestic fuel and power VAT base built from `electricity_consumption` and
`gas_consumption` (PolicyEngine/policyengine-uk#2166) changes what the survey
coverage applies to. If those energy inputs are already calibrated to an
aggregate, they should not be divided by the survey coverage again, and the
reconciled energy part of `reduced_rate_vat_consumption` should come out of the
base used to derive it.
