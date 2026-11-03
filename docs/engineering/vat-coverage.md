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
- `gov.simulation.vat.survey_consumption_coverage` (0.69): the share of
  household VAT liability that the dataset's consumption captures. This
  depends on the dataset's consumption imputation and must be re-derived when
  the default dataset changes.

The incidence assumption is that every pound of receipts, including VAT that
government, charities and exempt businesses pay on their inputs, is passed on
to households in proportion to their own VAT-liable spending.

These two factors replace `gov.simulation.microdata_vat_coverage`, a single
undated 0.38 added in January 2023 against an older LCFS-based consumption
imputation, with no derivation recorded. Its product with the October 2026
datasets put 2024-25 VAT 24% above OBR receipts on Microcosm UK 2024-25
(`f9d1922c`) and 71% above on Enhanced FRS 2024-25 (policyengine-uk-data
1.56.16).

`gov.simulation.microdata_vat_coverage` is kept as a deprecated parameter so
that existing reforms to it still work. Its value is now the product of the two
factors (0.483). If a reform sets it to any other value, `vat` uses that value
in place of the two factors (`policyengine_uk/utils/vat.py`), and
`baseline_vat`, which reads the unreformed parameters, keeps the two factors.
New reforms should change the two factors instead.

## Which datasets the factor applies to

The survey coverage of 0.69 matches 2024-25 receipts on one dataset: the
certified Microcosm UK 2024-25 national release `a6299504`. It does not carry
over to other datasets, because their consumption imputations capture a
different share of household VAT. On Enhanced FRS 2024-25
(policyengine-uk-data 1.58.1) it puts total `vat` 38% above receipts in
2024-25, falling to 32% in 2026-27 (see
[Derivation on `a6299504`](#derivation-on-a6299504-november-2026)). Re-derive
the coverage, with the calculation below, whenever the dataset it should match
changes.

As of November 2026, policyengine.py certifies `a6299504`: its commit
`324ecad65` certified the cut, release 6.11.1 shipped it, and release 6.12.0
still certifies it. The coverage comes from that cut, in
[Derivation on `a6299504`](#derivation-on-a6299504-november-2026).
policyengine.py certified `6cba5d71` before it, on 20 October 2026 (commit
`a66e883c4`). policyengine.py#715 proposed `a133f37a` and closed unmerged, so
no policyengine.py release certified that cut. Before the energy split, 0.67
put VAT 7.5% to 10.3% above receipts on `a133f37a` (see
[Later Microcosm cuts](#later-microcosm-cuts-24-october-2026)).

## Derivation on `a6299504` (November 2026)

The parameter takes this derivation's value. The model figures in this section
come from runs on 3 November 2026 with policyengine-uk 2.157.1 (commit
`36bbbf42f`), policyengine-core 3.33.2, NumPy 2.5.4, pandas 3.1.0 and Python
3.14, with `HUGGING_FACE_TOKEN` and `POLICYENGINE_UK_DEFAULT_DATASET` unset.
That commit ships a coverage of 0.67; the runs at 0.69 set
`gov.simulation.vat.survey_consumption_coverage` to 0.69 in every year by
reform.

### Inputs

| Input | Value | Source |
|---|---|---|
| Microcosm UK 2024-25 national release | `microcosm_uk_2024_25.h5`, Hugging Face dataset repository `policyengine/populace-uk-private`, tag `microcosm-uk-2024-25-national-20261025T091414Z-a6299504` (revision `994cac89d902af9a985af7c1182d74717a582ce0`), SHA-256 `b96a8cd625b645a409c063b1de5158532708a2f0d3c3897a794a8fb0bbd5064e`, 342,348,841 bytes; 78,234 households and 181,842 persons, 28.87 million weighted households in 2024-25 | Private repository |
| Build | `uk-frs-calibration-attempt-20261025T091414Z-a6299504`, at Microcosm code pin `67ee2ddf3`, with policyengine-uk 2.151.0 | PolicyEngine/microcosm |
| Certification | policyengine.py commit `324ecad65` ("Certify the Microcosm UK national a6299504 with policyengine-uk 2.151.0", 26 October 2026, through policyengine.py#720); release 6.11.1 (27 October 2026) shipped it, and release 6.12.0 (2 November 2026) still certifies it | PolicyEngine/policyengine.py |
| VAT receipts | £170.994bn (2024-25 outturn), £180.169bn (2025-26), £187.704bn (2026-27) | OBR, Economic and fiscal outlook March 2026, detailed forecast tables: receipts, sheet "3.8 Current receipts (on a cash basis)", row 13 "Value added tax", cells D13, E13 and F13 (see below) |
| Enhanced FRS 2024-25 | `enhanced_frs_2024_25.h5`, Hugging Face model repository `policyengine/policyengine-uk-data-private`, policyengine-uk-data 1.58.1 (revision `2526edbbb687a3b54dbb11272e5389e4b62d2ac2`, SHA-256 `056e80fd8e9151d78f432a25cde863340baee81304c6216a37fb575ce8563784`, 128,409,762 bytes), the release that `policyengine_uk/tests/certified_dataset.yaml` names | Private repository |
| Household share of VAT liabilities | 0.7 | `household_share_of_receipts` |
| Ready reckoner | £8.8bn for one point on the standard rate, 2026-27 | HMRC, Direct effects of illustrative tax changes (June 2025) |
| Statutory rates | 20% standard, 5% reduced | `gov.hmrc.vat` |

Microcosm's fit for this cut holds `obr.vat` out under a measure exclusion
(PolicyEngine/microcosm#1278) that a Microcosm maintainer approved on
24 October 2026 and that expires on 24 January 2027, so the fitted weights
don't target the receipts that this derivation compares VAT with. The cut's
calibration diagnostics carry one warn-only VAT warning,
`uk_consumption_drift`: the total `full_rate_vat_base` moves by more than 2%
of its design value between the design and the final weights.

OBR publishes the receipts workbook at
<https://obr.uk/docs/d055fbf02d5b3g6jq8l2/efo-march-2026-detailed-forecast-tables-receipts.xlsx>.
On 3 November 2026 that URL served 187,899 bytes with SHA-256
`f65b6cb7f96931d4abd85940794eb60f6f65afca8bbf16c74a4548bf92766a28`, last
modified on 3 March 2026, and the
[Internet Archive's copy](https://web.archive.org/web/20261007143332/https://obr.uk/docs/d055fbf02d5b3g6jq8l2/efo-march-2026-detailed-forecast-tables-receipts.xlsx)
holds the same bytes. In sheet "3.8 Current receipts (on a cash basis)", row 13
"Value added tax" gives, in £ billion, D13 = 170.994 (2024-25 outturn),
E13 = 180.16893868541794 (2025-26) and F13 = 187.70436725810845 (2026-27). The
sheet's note in row 66 reads "All tax lines prior to accruals adjustments on
tax line are on a cash basis".

### Method

The coverage follows the energy-split method in
[the energy section](#energy-bills-are-not-grossed-up):

```text
pre-scaling non-energy VAT = 0.20 x sum(full_rate_vat_consumption)
                           + 0.05 x sum(reduced_rate_vat_consumption)
energy-bill VAT            = sum(domestic_energy_vat)
survey coverage            = pre-scaling non-energy VAT
                             / (0.7 x (OBR VAT receipts - energy-bill VAT))
```

Every sum weights households by `household_weight`.

A run of the whole cut in one process needed more than the 8 GiB of memory
available, so the runs split it into ten household chunks. Chunk k holds every
tenth household from the k-th, by sorted `household_id`, with its persons and
benefit units. Each chunk runs `Microsimulation` on
`extend_single_year_dataset(chunk, parameters, end_year=2026)`. Each
household's VAT depends only on its own inputs: `full_rate_vat_consumption`
multiplies the household's `consumption` by its own
`full_rate_vat_expenditure_rate`, the uprating multiplies each household's
inputs by growth factors, and `vat` divides each household's statutory
liability by one scalar factor. So weighted VAT totals over the ten chunks sum
exactly to the whole cut's. As a check, for each VAT input and `vat` in
2024-25 to 2026-27, chunk 0 matched a separate run of the same households to
the last digit, and chunk 0's two halves summed to it within 2.7e-16 of the
total.

### Results

At the coverage of 0.67 that `36bbbf42f` ships:

| Fiscal year | Standard-rated base | Reduced-rated base | Pre-scaling non-energy VAT | Energy-bill VAT | OBR VAT receipts | Coverage | Total `vat` at 0.67 | Against receipts |
|---|---|---|---|---|---|---|---|---|
| 2024-25 | £407.40bn | £0.00bn | £81.48bn | £2.33bn | £170.994bn (outturn) | 0.690 | £176.06bn | +3.0% |
| 2025-26 | £422.51bn | £0.00bn | £84.50bn | £2.42bn | £180.169bn | 0.679 | £181.09bn | +0.5% |
| 2026-27 | £433.75bn | £0.00bn | £86.75bn | £1.75bn | £187.704bn | 0.666 | £185.18bn | -1.3% |

Unrounded (£): standard-rated base 407,399,379,048, 422,514,711,572 and
433,745,364,638; energy-bill VAT 2,328,998,935, 2,415,410,320 and
1,749,888,519; pre-scaling non-energy VAT 81,479,875,810, 84,502,942,314 and
86,749,072,928; total `vat` at 0.67 176,060,075,948, 181,087,241,846 and
185,178,679,581. The run read private school fees' share of receipts as 0,
0.008353 and 0.008311.

### Value

The parameter takes 0.69 (product 0.483), the 2024-25 value: as in the
[`f9d1922c` derivation](#earlier-derivation-on-f9d1922c-october-2026), the
latest outturn year sets it. Receipts for later years come from OBR forecasts,
so the factor stays undated. The coverage falls 3.4% from 2024-25 to 2026-27.

### Totals at 0.67 and 0.69

| Dataset | Fiscal year | Total `vat` at 0.67 | Against receipts | Total `vat` at 0.69 | Against receipts |
|---|---|---|---|---|---|
| Microcosm UK 2024-25 (`a6299504`) | 2024-25 | £176.06bn | +3.0% | £171.02bn | +0.02% |
| Microcosm UK 2024-25 (`a6299504`) | 2025-26 | £181.09bn | +0.5% | £175.91bn | -2.4% |
| Microcosm UK 2024-25 (`a6299504`) | 2026-27 | £185.18bn | -1.3% | £179.86bn | -4.2% |
| Enhanced FRS 2024-25, uk-data 1.58.1 | 2024-25 | £242.54bn | +41.8% | £235.58bn | +37.8% |
| Enhanced FRS 2024-25, uk-data 1.58.1 | 2025-26 | £249.37bn | +38.4% | £242.22bn | +34.4% |
| Enhanced FRS 2024-25, uk-data 1.58.1 | 2026-27 | £255.28bn | +36.0% | £247.93bn | +32.1% |

Unrounded Microcosm totals at 0.69 (£): 171,024,393,280, 175,908,348,963 and
179,861,903,668. The Enhanced FRS run used the whole file in one process. On
that file the same calculation gives a coverage of 0.954, 0.939 and 0.921, from
a standard-rated base of £563.06bn, £583.95bn and £599.47bn, a reduced-rated
base of £0.00bn, and energy-bill VAT of £2.43bn, £2.43bn and £1.76bn.

Total `vat` leaves out `private_school_vat`, which the receipts include: about
£1.5bn a year from 2025-26 on HMRC's costing (see
[Private school VAT](#private-school-vat-splitting-the-existing-receipts-total)).
Model year 2024 has no school charge.

### Bound

On `a6299504` two routes bound the coverage, at a household share of 0.7:

- receipts across 2024-25 to 2026-27 give 0.666 to 0.690;
- the ready reckoner, which does not use the level of receipts: one point on
  the standard rate raises £4.34bn before scaling in 2026-27 (1% of
  £433.75bn), so, leaving out the school share, matching HMRC's £8.8bn needs
  a product of 0.493 (coverage 0.704).

So the coverage lies between 0.666 and 0.704, and 0.69 sits inside that range.
At 0.69, a run that sets the standard rate to 21% for 2026-27 alone raises
total `vat` in that year from £179.862bn to £188.767bn, by £8.906bn, exceeding
the ready reckoner by 1.2%. That rise matches 1% of the 2026-27 standard-rated
base, times one minus the school share, over the product:
£4,337,453,646 x (1 - 0.008311) / 0.483 = £8,905,600,556, within £8,968 of the
run's £8,905,591,588.

### Reproducing

The datasets sit in private Hugging Face repositories. Anyone with
PolicyEngine access can rerun the calculation; anyone else can check the
arithmetic from the published aggregates above.

```python
from huggingface_hub import hf_hub_download
from policyengine_uk import Microsimulation

path = hf_hub_download(
    "policyengine/populace-uk-private",
    "microcosm_uk_2024_25.h5",
    repo_type="dataset",
    revision="994cac89d902af9a985af7c1182d74717a582ce0",
)
sim = Microsimulation(dataset=path)
# OBR March 2026 EFO, table 3.8, cash-basis VAT receipts
receipts = {2024: 170.994e9, 2025: 180.169e9, 2026: 187.704e9}
for year, obr in receipts.items():
    p = sim.tax_benefit_system.parameters(f"{year}-01-01").gov.hmrc.vat
    full = sim.calculate("full_rate_vat_consumption", year).sum()
    reduced = sim.calculate("reduced_rate_vat_consumption", year).sum()
    energy = sim.calculate("domestic_energy_vat", year).sum()
    raw = full * p.standard_rate + reduced * p.reduced_rate
    print(year, raw / 1e9, energy / 1e9, raw / (0.7 * (obr - energy)))
```

A run of the whole cut in one process needed more than 8 GiB of memory, so the
runs above summed ten household chunks (see [Method](#method)).

For Enhanced FRS, download `enhanced_frs_2024_25.h5` from the model repository
`policyengine/policyengine-uk-data-private` at policyengine-uk-data 1.58.1
(`revision="2526edbbb687a3b54dbb11272e5389e4b62d2ac2"`). For an earlier cut,
set `revision` to the tag or full revision that its inputs table gives.

## Earlier derivation on `f9d1922c` (October 2026)

This section records the October 2026 derivation on `f9d1922c`, which set the
coverage at 0.67 before the energy split. The
[`a6299504` derivation](#derivation-on-a6299504-november-2026) replaces it.

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
(policyengine-uk-data 1.58.1) at 0.67 that difference came to -£5.5m to
-£142.5m a year from 2025-26 to 2031-32, at most 0.06% of VAT (Aggregate impact
run
[40116746457](https://github.com/PolicyEngine/policyengine-uk/actions/runs/40116746457),
24 October 2026).

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

The parameter took the Microcosm 2024-25 value, 0.67 (product 0.469), the
latest outturn year.

With that product, the gross amount against receipts was as below, before
energy bills were split out. On the certified Enhanced FRS
(policyengine-uk-data 1.58.1) at 0.67, current-law `vat + private_school_vat`
came within 0.06% of the receipt-calibrated `G + E` (see above); no run
checked the other rows against that bound:

| Dataset | 2024-25 | 2025-26 | 2026-27 |
|---|---|---|---|
| Microcosm UK 2024-25 (`f9d1922c`) | £171.6bn (+0.4%) | £178.7bn (-0.8%) | £183.5bn (-2.2%) |
| Enhanced FRS 2024-25, uk-data 1.56.16 | £236.7bn (+38.4%) | £246.5bn (+36.8%) | £253.1bn (+34.8%) |
| Enhanced FRS 2024-25, uk-data 1.58.0 | £246.7bn (+44.3%) | £257.0bn (+42.6%) | £263.9bn (+40.6%) |

### Bound

Total VAT depends only on the product, so the household share being a
rounded "around 70%" changes how the product is split between the two factors,
not the totals. On `f9d1922c` two routes bounded the product:

- the receipts route across 2024-25 to 2026-27: 0.459 to 0.471 (coverage 0.655
  to 0.672);
- the ready reckoner, which does not use the level of receipts: one point on
  the standard rate raised £4.24bn before scaling in 2026-27 (1% of
  £423.66bn), so matching HMRC's £8.8bn needed a product of 0.481 (coverage
  0.688).

So on `f9d1922c` the product lay between 0.459 and 0.481, and the coverage
between 0.655 and 0.688 at a household share of 0.7. The value then used,
0.469 (0.67), sat inside that range, and the totals it gave came within 2.2% of
receipts from 2024-25 to 2026-27. The implied product moved by less than 3%
over those years.

### Reproducing

Run the snippet in
[Derivation on `a6299504`](#derivation-on-a6299504-november-2026) with
`revision="f9d1922cddab6b54a0dd37794a9bac74e3780c88"`. For the pre-split rows
above, run it on policyengine-uk as of #2187, before energy bills left
`reduced_rate_vat_consumption`, and divide pre-scaling VAT by the receipts
themselves (`raw / obr / 0.7`). For Enhanced FRS 1.56.16 or 1.58.0, download
`enhanced_frs_2024_25.h5` at that release tag (for example
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

On the same inputs as the
[`f9d1922c` derivation](#earlier-derivation-on-f9d1922c-october-2026):

| Dataset | Year | Pre-scaling non-energy VAT | Energy-bill VAT | OBR VAT receipts | Survey coverage |
|---|---|---|---|---|---|
| Microcosm UK 2024-25 (`f9d1922c`) | 2024-25 | £79.23bn | £1.99bn | £171.0bn (outturn) | 0.670 |
| Microcosm UK 2024-25 (`f9d1922c`) | 2025-26 | £82.51bn | £2.01bn | £180.2bn | 0.662 |
| Microcosm UK 2024-25 (`f9d1922c`) | 2026-27 | £84.73bn | £1.40bn | £187.7bn | 0.650 |
| Enhanced FRS 2024-25, uk-data 1.56.16 | 2024-25 | £109.39bn | £2.35bn | £171.0bn (outturn) | 0.927 |
| Enhanced FRS 2024-25, uk-data 1.58.0 | 2024-25 | £114.06bn | £2.44bn | £171.0bn (outturn) | 0.967 |

The pre-scaling non-energy VAT is the standard-rated part alone, since the
generic reduced-rate base is empty once domestic fuel and power is taken out.
On `f9d1922c` the 2024-25 value rounded to the same 0.67 as the pre-split
derivation, so the energy split left the parameter at 0.67, and the `f9d1922c`
bound still held (0.650 to 0.670 by receipts, 0.688 by the ready reckoner).
With 0.67, total `vat` on `f9d1922c` came within 0.1% of 2024-25 receipts and
fell 3.0% below them in 2026-27; on Enhanced FRS it exceeded 2024-25 receipts
by 38% (1.56.16) or 44% (1.58.0). The
[`a6299504` derivation](#derivation-on-a6299504-november-2026) sets the
current value.

To reproduce these rows, run the snippet in
[Derivation on `a6299504`](#derivation-on-a6299504-november-2026) with each
dataset's revision, and for Enhanced FRS with the repository and file that
section gives. The snippet subtracts
`sim.calculate("domestic_energy_vat", year).sum()` from the receipts before
dividing.

## Private school VAT: splitting the existing receipts total

The OBR VAT total already includes VAT on private school fees. HMRC's
[VAT-only costing](https://www.gov.uk/government/publications/vat-on-private-school-fees/applying-vat-to-private-school-fees)
(Autumn Budget 2024 Table 5.1, certified by the OBR) is £460m in 2024-25,
£1,505m in 2025-26, £1,560m in 2026-27, £1,610m in 2027-28, £1,665m in
2028-29 and £1,725m in 2029-30. Adding a separate school VAT head to the
gross amount above would count that receipt twice. The model instead takes
the fees' share of receipts out of the gross amount, which leaves the survey
coverage unchanged.

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

Measured on the certified Enhanced FRS at a coverage of 0.67 (Aggregate impact
run
[40116746457](https://github.com/PolicyEngine/policyengine-uk/actions/runs/40116746457),
24 October 2026), the official share changes current-law combined receipts by
-£0.14bn in 2025-26, -£0.13bn in 2026-27, -£0.10bn in 2027-28, -£0.08bn in
2028-29 and -£0.01bn in 2029-30, at most 0.06% of that dataset's VAT. Two
overstatements nearly offset in that run: VAT exceeded OBR receipts by 40%
(£252.5bn against £180.2bn in 2025-26), and the modelled school charge came to
£1.95bn, against HMRC's £1.505bn, because
attendance is imputed for 751,000 weighted pupils (policyengine-uk-data issue
568). The difference belongs to those two calibrations, not to the split.

The split leaves the receipts check for the coverage factor unchanged. Model
year 2024 has no school charge and a zero share, so, using the rounded 2024-25
inputs for `a6299504`, `81.48 / (0.69 * 0.7) + 2.33 = £171.026bn`, against
OBR's £170.994bn: 0.02% above receipts. The run at 0.69 gives £171.02bn on the
unrounded inputs (see
[Derivation on `a6299504`](#derivation-on-a6299504-november-2026)). With 0.67,
the rounded `f9d1922c` inputs gave `79.23 / (0.67 * 0.7) + 1.99 = £170.924bn`,
about 0.04% below receipts. The existing differences from receipts, including
Enhanced FRS's larger overstatement, still require dataset-specific
calibration. Aggregate impact CI compares the combined VAT report group
against the PR's base.

Model year 2024 represents 2024-25 but reads annual policy before the
January 2025 commencement, so `P0` and the share are both zero for that
year. The £460m part-year receipt (0.27% of £170,994m) remains in general
VAT; this change does not model its separate timing.

## Later Microcosm cuts (24 October 2026)

These runs predate the energy split above, so they use the formula in
[the `f9d1922c` derivation](#earlier-derivation-on-f9d1922c-october-2026). They record why the coverage has to be
re-derived (PolicyEngine/policyengine-uk#2633). They do not set the parameter.

| Input | Value |
|---|---|
| `a133f37a` | Hugging Face `policyengine/populace-uk-private`, tag `microcosm-uk-2024-25-national-20261023T075039Z-a133f37a` (revision `c3a751d9`), SHA-256 `64f83900ca3a1242fb017585234844ce89f743d32e41cd2b6558057777f914aa` |
| `6cba5d71` | tag `microcosm-uk-2024-25-national-20261019T083323Z-6cba5d71` (revision `bb225848`), SHA-256 `810ba980005a8b907cb51464279fa5e0125464b7af9a4871b7f6744c30951ece` |

The `a133f37a` rows were computed with policyengine-uk 2.152.7 and
policyengine-core 3.33.2, and again with policyengine-uk 2.147.2 and
policyengine-core 3.33.3, which give the same totals. The `6cba5d71` rows were
computed with policyengine-uk 2.147.2 and policyengine-core 3.33.3.

| Dataset | Year | Standard-rated base | Reduced-rated base | Pre-scaling VAT | Receipts | Product | Survey coverage |
|---|---|---|---|---|---|---|---|
| Microcosm UK 2024-25 (`a133f37a`) | 2024-25 | £435.60bn | £26.76bn | £88.46bn | £171.0bn | 0.517 | 0.739 |
| Microcosm UK 2024-25 (`a133f37a`) | 2025-26 | £453.65bn | £27.87bn | £92.12bn | £180.2bn | 0.511 | 0.730 |
| Microcosm UK 2024-25 (`a133f37a`) | 2026-27 | £465.85bn | £28.62bn | £94.60bn | £187.7bn | 0.504 | 0.720 |
| Microcosm UK 2024-25 (`6cba5d71`) | 2024-25 | | | £88.51bn | £171.0bn | 0.518 | 0.739 |
| Microcosm UK 2024-25 (`6cba5d71`) | 2025-26 | | | £92.18bn | £180.2bn | 0.512 | 0.731 |
| Microcosm UK 2024-25 (`6cba5d71`) | 2026-27 | | | £94.66bn | £187.7bn | 0.504 | 0.720 |

These runs, all before the energy split, show the gap:

- With 0.67, total `vat` on `a133f37a` was 10.3%, 9.0% and 7.5% above receipts
  in 2024-25 to 2026-27 (£188.61bn, £196.43bn and £201.71bn).
- On `6cba5d71`, a reform run that raises the standard rate from 20% to 21%
  changed total `vat` and `gov_balance` by £9.94bn in 2026-27 and £9.68bn in
  2025-26 (reform minus baseline; policyengine-uk 2.135.7 and 2.152.6 agree).
  That is 12.9% above HMRC's £8.8bn ready reckoner.
- With 0.74 (product 0.518), total `vat` on `a133f37a` was 0.1%, 1.3% and 2.7%
  below receipts.
- With 0.74, a one-point reform run cost £8.99bn in 2026-27, 2.2% above the
  ready reckoner.
