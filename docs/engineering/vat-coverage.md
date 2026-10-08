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
Enhanced FRS 2024-25.

`gov.simulation.microdata_vat_coverage` is kept as a deprecated parameter so
that existing reforms to it still work. Its value is now the product of the two
factors (0.469). If a reform sets it to any other value, `vat` and
`baseline_vat` use that value in place of the two factors
(`policyengine_uk/utils/vat.py`); otherwise they use the two factors. New
reforms should change the two factors instead.

## Derivation (October 2026)

The product of the two factors is the dataset's pre-scaling VAT divided by
receipts for the same year. The survey coverage is that product divided by the
household share.

| Dataset | Year | Pre-scaling VAT | OBR VAT receipts | Product | Survey coverage |
|---|---|---|---|---|---|
| Microcosm UK 2024-25 (populace-uk-private `f9d1922c`) | 2024-25 | £80.5bn | £171.0bn (outturn) | 0.471 | 0.672 |
| Microcosm UK 2024-25 | 2025-26 | £83.8bn | £180.2bn | 0.465 | 0.665 |
| Microcosm UK 2024-25 | 2026-27 | £86.1bn | £187.7bn | 0.459 | 0.655 |
| Enhanced FRS 2024-25 | 2024-25 | £111.0bn | £171.0bn (outturn) | 0.649 | 0.927 |

Receipts are the cash-basis VAT line of OBR March 2026 EFO detailed forecast
table 3.8. Model year 2024 is the 2024-25 fiscal year.

HMRC's ready reckoner gives an independent check that does not use the level
of receipts: one percentage point on the standard rate raises £8.8bn in
2026-27 (Direct effects of illustrative tax changes, June 2025). On Microcosm
UK 2024-25, one point on the standard rate raises £4.24bn before scaling, so
matching HMRC needs a product of 0.48, within 3% of the level-based 0.469.

The value is set against the certified Microcosm UK 2024-25 national release.
On Enhanced FRS 2024-25 it puts 2024-25 VAT about 38% above receipts (it was
71% above with 0.38). The implied product moves by less than 3% between
2024-25 and 2026-27, so the factors are not dated by year.

## Reproducing

```python
from policyengine_uk import Microsimulation

sim = Microsimulation(dataset="microcosm_uk_2024_25.h5")
year = 2024
p = sim.tax_benefit_system.parameters(f"{year}-01-01").gov.hmrc.vat
raw = (
    sim.calculate("full_rate_vat_consumption", year).sum() * p.standard_rate
    + sim.calculate("reduced_rate_vat_consumption", year).sum() * p.reduced_rate
)
obr_receipts = 170.994e9  # OBR March 2026 EFO, table 3.8, 2024-25
product = raw / obr_receipts
print(product, product / 0.7)
```

## Interaction with an explicit energy VAT base

A domestic fuel and power VAT base built from `electricity_consumption` and
`gas_consumption` (PolicyEngine/policyengine-uk#2166) changes what the survey
coverage applies to. If those energy inputs are already calibrated to an
aggregate, they should not be divided by the survey coverage again, and the
reconciled energy part of `reduced_rate_vat_consumption` should come out of the
base used to derive it.
