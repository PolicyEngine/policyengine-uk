# VAT grossing to receipts

`vat` and `baseline_vat` compute the statutory liability on each household's
recorded consumption (the standard rate on `full_rate_vat_consumption` plus
the reduced rate on `reduced_rate_vat_consumption`) and divide it by two
factors. This gross amount, plus VAT on households' energy bills (see
[Energy bills are not grossed up](#energy-bills-are-not-grossed-up)), is
calibrated to total VAT receipts. The private school component is then
allocated to `private_school_vat`, as explained below, so the receipts
comparison uses `vat + private_school_vat`:

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
sums from `Microsimulation`, computed with policyengine-uk as of #2187 (before
energy bills were split out, see below) and policyengine-core 3.33.2.

### Formula

```
pre-scaling VAT = 0.20 x sum(full_rate_vat_consumption)
                + 0.05 x sum(reduced_rate_vat_consumption)
product         = pre-scaling VAT / OBR VAT receipts      (same year)
survey coverage = product / household share (0.7)
```

Dividing each household's statutory VAT by the product gives the gross
amount, `G`; VAT on energy bills, `E`, is added to it without grossing (see
[Energy bills are not grossed up](#energy-bills-are-not-grossed-up)). At
current law, total `vat + private_school_vat` is close to `G + E` but not
equal to it: combined receipts are
`(1 - s) * sum(w * G) + sum(w * E) + sum(w * P0)` (see the receipt-partition
derivation below), so they differ from `G + E` by
`sum(w * P0) - s * sum(w * G)`. On the certified Enhanced FRS
(policyengine-uk-data 1.58.1) that difference is -£5.5m to -£142.5m a year from
2025-26 to 2031-32, at most 0.06% of VAT (Aggregate impact run
[40116746457](https://github.com/PolicyEngine/policyengine-uk/actions/runs/40116746457)).

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

With that product, the gross amount against receipts was as below, before
energy bills were split out. On the certified Enhanced FRS
(policyengine-uk-data 1.58.1), current-law `vat + private_school_vat` is
within 0.06% of the receipt-calibrated `G + E` (see above); the other rows
weren't checked against that bound:

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

## Energy bills are not grossed up


VAT on domestic electricity and gas is charged on each household's own bills
(`domestic_energy_vat`, PolicyEngine/policyengine-uk#2166), and the ONS domestic
fuel and power share of spending comes out of the generic reduced-rate share.
Those bills are calibrated to national energy use (NEED), and households bear
VAT on them in full, so neither factor applies to them:

```
vat = (standard rate x full_rate_vat_consumption
       + reduced rate x reduced_rate_vat_consumption)
      / (survey_consumption_coverage x household_share_of_receipts)
      + domestic_energy_vat
```

The electricity and gas inputs are priced including 5% VAT by the data build
(Microcosm UK at DESNZ Quarterly Energy Prices average prices paid; the legacy
Enhanced FRS at Ofgem price cap unit rates), so `domestic_energy_vat` charges the statutory rates on the
input divided by 1.05. The divisor is the fixed price-basis parameter
`gov.simulation.vat.energy_input_price_basis_rate`, not the statutory reduced
rate, so a reform to a VAT rate leaves the VAT-exclusive base unchanged.

Dividing energy VAT by the household share as well would put part of
government, charity and exempt-business VAT on electricity bills, and a zero
rate on domestic electricity would then cost 1/0.7 times the VAT households
actually pay on it.

With energy split out, the coverage is derived against receipts net of energy
VAT: coverage = pre-scaling non-energy VAT / (0.7 x (receipts - energy VAT)).

On the same inputs as the derivation above:

| Dataset | Year | Pre-scaling non-energy VAT | Energy-bill VAT | OBR VAT receipts | Survey coverage |
|---|---|---|---|---|---|
| Microcosm UK 2024-25 (`f9d1922c`) | 2024-25 | £79.23bn | £1.99bn | £171.0bn (outturn) | 0.670 |
| Microcosm UK 2024-25 (`f9d1922c`) | 2025-26 | £82.51bn | £2.01bn | £180.2bn | 0.662 |
| Microcosm UK 2024-25 (`f9d1922c`) | 2026-27 | £84.73bn | £1.40bn | £187.7bn | 0.650 |
| Enhanced FRS 2024-25, uk-data 1.56.16 | 2024-25 | £109.39bn | £2.35bn | £171.0bn (outturn) | 0.927 |
| Enhanced FRS 2024-25, uk-data 1.58.0 | 2024-25 | £114.06bn | £2.44bn | £171.0bn (outturn) | 0.967 |

The pre-scaling non-energy VAT is the standard-rated part alone, since the
generic reduced-rate base is empty once domestic fuel and power is taken out.
The Microcosm 2024-25 value rounds to the same 0.67 as the derivation above,
so the parameter is unchanged, and the bound above still holds (0.650 to 0.670
by receipts, 0.688 by the ready reckoner). With it, total `vat` on Microcosm
is within 0.1% of 2024-25 receipts and 3.0% below in 2026-27; on Enhanced FRS
it is 38% (1.56.16) or 44% (1.58.0) above 2024-25 receipts.

To reproduce, run the snippet above on this version and subtract
`sim.calculate("domestic_energy_vat", year).sum()` from the receipts before
dividing.

## Private school VAT: splitting the existing receipts total

The OBR VAT total already includes VAT on private school fees. HMRC's
[VAT-only costing](https://www.gov.uk/government/publications/vat-on-private-school-fees/applying-vat-to-private-school-fees)
(Autumn Budget 2024 Table 5.1, certified by the OBR) is £460m in 2024-25,
£1,505m in 2025-26, £1,560m in 2026-27, £1,610m in 2027-28, £1,665m in
2028-29 and £1,725m in 2029-30. Adding a separate school VAT head to the
gross amount above would count that receipt twice. The model instead takes
the fees' share of receipts out of the gross amount, keeping the survey
coverage at 0.67.

For each household, let `G` be the grossed-up VAT on recorded consumption
other than energy bills (the statutory liability divided by the two factors),
`E` be `domestic_energy_vat`, `s` be
`gov.simulation.vat.private_school_share_of_receipts`, `P0` be
`baseline_private_school_vat` (baseline policy with this simulation's
attendance, fee and VAT-basis assumptions) and `P` be `private_school_vat`:

```text
vat          = G  * (1 - s) + E
baseline_vat = G0 * (1 - s) + E0
combined VAT = vat + P
```

The share comes out of `G` only. School fees are not energy bills, and `E`
is not grossed up, so a reform to the VAT on energy bills changes `vat` by
exactly the change in `E`.

`s` is the costing divided by OBR cash-basis VAT receipts for the same
fiscal year (October 2026 EFO, table 4.8; 2025-26 is outturn):

| Fiscal year | School-fee VAT (£m) | VAT receipts (£m) | Share |
|---|---:|---:|---:|
| 2025-26 | 1,505 | 179,861 | 0.8368% |
| 2026-27 | 1,560 | 186,154 | 0.8380% |
| 2027-28 | 1,610 | 193,974 | 0.8300% |
| 2028-29 | 1,665 | 203,284 | 0.8190% |
| 2029-30 | 1,725 | 211,701 | 0.8148% |

Before the October 2026 EFO the shares used the March 2026 EFO's receipts
(table 3.8), 0.8353% in 2025-26 to 0.8094% in 2029-30. The coverage
calibration above still uses the March 2026 EFO's 2024-25 outturn, which the
October 2026 EFO does not revise.

The 2029-30 share is held after it. Each value starts on 1 April, so a model
year reads its fiscal year's share. `vat` and `baseline_vat` both read it
from the simulation's own parameters, as `baseline_private_school_vat` reads
its assumptions; the baseline parameter tree reads 1 January, before the
fiscal year's value takes effect.

Properties of the split:

- Because `0 <= s < 1` and `E` does not depend on `s`, the allocation never
  makes a household's VAT negative where `G` and `E` are non-negative, and
  repealing the school charge cannot either.
- `vat` reads neither attendance nor fees. Restoring the school exemption sets
  `P` to zero and leaves `vat` unchanged, so receipts fall by the weighted
  school charge, `sum(w * P0)`, with no second grossing factor. A contributed
  rate moves only `P`.
- A standard-rate change moves `G * (1 - s)` and `P`, each on its own base:
  recorded consumption and the fees. `E` moves only with the domestic
  electricity and reduced rates.
- With household weights `w`, current-law combined receipts are
  `sum(w * G) - s * sum(w * G) + sum(w * E) + sum(w * P0)`. They equal the
  receipt-calibrated total `sum(w * G) + sum(w * E)` when the population's
  school charge is the share `s` of its grossed-up VAT, and otherwise differ
  from it by `sum(w * P0) - s * sum(w * G)`.
- `s` is a share of total receipts, but `G` is calibrated to receipts net of
  energy-bill VAT. Where `G` matches receipts net of energy-bill VAT exactly,
  `s * sum(w * G)` falls short of the costing by `s` times energy-bill VAT:
  on `f9d1922c`'s 2025-26 energy-bill VAT, 0.8368% of £2.01bn, about £17m
  (arithmetic on the energy table above, not a run).

The earlier design subtracted each household's own school charge from its
own gross VAT. Combined receipts then equalled `G` household by household,
but a pupil with little recorded consumption had negative general VAT, which
a repeal left in place. On the certified Enhanced FRS (policyengine-uk-data
1.58.1), before energy bills were split out, that made general VAT negative
for 549 households with non-negative gross VAT in 2025-26 (306,750 weighted
households, -£0.58bn), rising to 572 in 2030-31.

A share measured on each simulation's own population,
`sum(w * P0) / sum(w * G)`, would preserve combined receipts exactly, and was
considered. It makes every household's general VAT depend on the imputed
attendance of every other household, and attendance is imputed from net
income. Raising any household's income tax, National Insurance or council tax
could then move every household's VAT, by its gross VAT times the change in
the share. The aggregate-impact counted-once check fails a head wherever such
a response is one for one, as it did for `vat` in fewer than 10 households
under the earlier design; spreading the response to every household makes
that coincidence likelier. A household situation would also measure its own
school charge against its own VAT. The official share keeps each household's
VAT a function of its own consumption.

Measured on the certified Enhanced FRS (Aggregate impact run
[40116746457](https://github.com/PolicyEngine/policyengine-uk/actions/runs/40116746457)),
the official share changes current-law combined receipts by -£0.14bn in
2025-26, -£0.13bn in 2026-27, -£0.10bn in 2027-28, -£0.08bn in 2028-29 and
-£0.01bn in 2029-30, at most 0.06% of that dataset's VAT. Two overstatements
nearly offset there: VAT is 40% above OBR receipts (£252.5bn against
£180.2bn in 2025-26), and the modelled school charge is £1.95bn, against
HMRC's £1.505bn, because
attendance is imputed for 751,000 weighted pupils (policyengine-uk-data issue
568). The difference belongs to those two calibrations, not to the split.

The receipts check for the coverage factor is unchanged. Model year 2024 has
no school charge and a zero share, so, using the rounded 2024-25 Microcosm
inputs in the energy table above, `79.23 / (0.67 * 0.7) + 1.99 = £170.924bn`,
compared with OBR's £170.994bn: about 0.04% below receipts. The existing
differences from receipts, including Enhanced FRS's larger overstatement, still require
dataset-specific calibration. Aggregate impact CI compares the combined VAT
report group against the PR's base.

Model year 2024 represents 2024-25 but reads annual policy before the
January 2025 commencement, so `P0` and the share are both zero for that
year. The £460m part-year receipt (0.27% of £170,994m) remains in general
VAT; this change does not model its separate timing.
