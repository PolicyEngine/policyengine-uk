# Economic assumptions

Year-on-year growth series for the UK economy used to uprate parameters and
calibrate the input dataset. The source of the default economic series is
[`yoy_growth.yaml`](./yoy_growth.yaml); downstream cumulative indices are
generated from it by
[`create_economic_assumption_indices.py`](./create_economic_assumption_indices.py).

The dedicated `capital_gains` growth/index paths copy GDP per capita by
default. A simulation can instead supply a versioned aggregate gains
projection, converted to per-record factors using population growth after
fiscal-year parameter processing. See the
[capital gains projection guide](../../../../docs/capital-gains-projection.md)
for its measurement contract, experimental scenario and remaining validation.
Both generated paths are read-only to parameter reforms; supply a
`CapitalGainsProjection` to change the gains path. Reforms to the underlying
GDP and population assumptions remain supported.

## Series

| Series                  | What it measures                                         | OBR/ONS source          |
|-------------------------|----------------------------------------------------------|-------------------------|
| `consumer_price_index`  | CPI year-on-year growth                                  | EFO Table 1.7           |
| `cpih`                  | CPI including owner-occupiers' housing costs             | EFO Table 1.7           |
| `consumer_price_index_ahc` | CPI excluding rents/maintenance/water (AHC measure)   | ONS ad hoc 3582; forecast derived by `utils/create_ahc_deflator.py` |
| `rpi`                   | Retail Price Index year-on-year growth                   | EFO Table 1.7           |
| `average_earnings`      | Average weekly earnings growth                           | EFO Table 1.6           |
| `non_labour_income`     | Non-labour household income growth                       | derived from EFO        |
| `road_fuel_volume`      | Petrol + diesel road-fuel clearances                     | HMRC Hydrocarbon Oils + OBR fuel-duty forecast |
| `petrol_spending_litre_proxy` | Spending growth that preserves road-fuel litres    | HMRC + OBR              |
| `diesel_spending_litre_proxy` | Same, for diesel                                   | HMRC + OBR              |
| `finance_ni.domestic_rates` | Average Northern Ireland domestic rates bill (regional plus district poundage) | DoF rate poundages, LPS rates paid, NI draft Budget 2026-29 |
| `stamp_duty_land_tax.residential` | SDLT receipts from residential property          | EFO receipts Table 3.7  |
| `stamp_duty_land_tax.non_residential` | SDLT receipts from non-residential property  | EFO receipts Table 3.7  |
| `business_rates.great_britain` | Business rates receipts, England, Scotland and Wales (cash) | EFO receipts, current receipts (cash basis): Table 3.8 in March 2026 |
| `business_rates.northern_ireland` | Northern Ireland business rates receipts      | EFO receipts Table 3.2  |

The four receipts series project the corporate SDLT and business rates
statistics (`gov.hmrc.stamp_duty.statistics`,
`gov.hmrc.business_rates.statistics`) from their latest outturn. Each is the
ratio of consecutive published receipts levels, to six decimals: outturn
growth for the EFO's outturn year (its outturn over the year before's outturn
in an earlier EFO), the EFO's forecast years, and after them the
`average_earnings` path. Years before the outturn year are kept, so each
index keeps its base year.

## Time horizons

Three horizons are stitched together for each OBR and ONS series (not
`finance_ni.domestic_rates`, which has its own method, below):

1. **Outturn** (history through 2024): ONS published data, copied from OBR
   detailed forecast tables.
2. **EFO forecast** (2025-2030): latest OBR Economic and Fiscal Outlook
   supplementary tables. The version currently checked in is **March 2026**;
   refresh after each new EFO.
3. **Long-run equilibrium** (2031-2073): constructed from OBR's long-run
   assumptions (Fiscal Risks and Sustainability report) and the long-run
   RPI-CPI wedge methodology.

## Dataset projection horizon

A single-year dataset is projected forward a year at a time to
`PROJECTION_END_YEAR` in
[`policyengine_uk/data/economic_assumptions.py`](../../../data/economic_assumptions.py),
now 2032 (fiscal year 2032-33). Each year's inputs are the year before's
times one plus the growth series
[`uprating_indices.yaml`](../../../data/uprating_indices.yaml) assigns them;
rent, council tax and student loan plans have their own functions there. Keep
`PROJECTION_END_YEAR` at or past the last year of the latest EFO, so that the
last year of a five-year costing is a dataset year.

For an explicitly finite CGT projection, the default extension ends at the
earlier of this constant and the scenario's final year. The cap applies to
the whole automatically extended dataset, not only its CGT columns.
Explicit out-of-span CGT projection requests raise an error. Increasing the
general horizon therefore does not extrapolate the experimental EOT series,
whose published determinant ends in FY2030–31.

CPI, CPIH, RPI, average earnings, road fuel and population run to 2073, but
several series end in 2030. Of those the projection uses, per-capita GDP and
mixed income, mortgage interest, council tax, social and private rents and
Northern Ireland domestic rates end in 2030. A parameter returns its latest
value after its last date, so in 2031 and 2032 these hold their 2030 growth
rate. That is an extrapolation, not an OBR forecast; replace it with the next
EFO's values once one covers those years.

After `PROJECTION_END_YEAR`, policyengine-core checks for a formula result
first, then an `uprating` attribute, then carries the last stored input forward.
Rent and council tax arrays are held flat; reported State Pension's formula
also holds its last value. Weighted totals can still rise with population
weights. In the legacy enhanced FRS 2024-25, recorded Pension Credit capital
falls to -1 because its formula's shared `benunit_reported_capital` input is
absent. That sentinel selects the household capital proxy. Likewise, the
stored tax-free savings exemption is replaced by ISA interest, which is zero
when its input is absent. Results beyond the horizon therefore have different
input semantics.

Direct programme capital inputs intentionally apply only in the periods
supplied. Preserving legacy survey capital beyond the horizon requires a
dataset compatibility change, such as materialising the survey's shared
benefit-unit capital without overwriting programme-specific countable capital.
Changing that formula to carry every direct input would alter situation
semantics.

Source coverage and processed parameter dates are distinct: fiscal-year
conversion materialises annual values through 2040, while cumulative economic
indices compound only through 2039. A later parameter lookup retains the final
scalar; for a raw growth series that repeats the growth rate, but for a
cumulative index it freezes the level. Extending the dataset to the raw
series' final year would therefore be both costly and inconsistent with Core
uprating after the cumulative-index horizon.

From 2031 onward, dataset projection also grows stored columns whose variables
have a class-level `uprating` index but are absent from `uprating_indices.yaml`.
It multiplies the previous year's value by the target-year index divided by
the previous-year index, preserving the growth Core applied after the former
2030 dataset horizon. `_unmapped_uprating_indices` discovers these variables
from the variable registry rather than maintaining another projection list.
The current registry has twelve eligible variables; the legacy enhanced FRS
2024-25 stores four of them: salary-sacrifice pension contributions, water and
sewerage charges, housing service charges and rail usage. Their historical
projection through 2030 retains its previous handling; correcting those
earlier mapping omissions is a separate change.

`domestic_energy_consumption`, `electricity_consumption` and `gas_consumption`
use a separate declaration-aware projector. Unlabelled datasets retain their
stored amounts through the projection horizon, preserving legacy inputs that
already use FY2026-27 prices. A dataset's explicit `energy_price_basis` opts
into the variables' existing cumulative annual OBR-CPI index as an interim
price proxy from its declared price year. The declaration covers only these
three inputs, independently of any other generic uprating exclusions. They
remain outside both the unconditional growth mapping and fallback, so no
second index grows them after 2030.

The declaration retains `calendar_year` or `fiscal_year` and its integer year.
The model uses the January 1 index level for the declared starting year for
both calendar and fiscal price periods. This shared start-year convention is
an approximation, rather than precise fiscal/calendar price alignment. The
projector applies `I[target year] / I[declared price year]` to the supplied
observation. A requested declared projection raises an error if either
January 1 precedes the selected index's earliest non-null value, including a
midyear start, or if the index has no usable history. Unlabelled inputs and
declarations with no stored energy inputs do not require index history. Each
projected child records its effective fiscal-year basis, while the source
observation keeps its original declaration.

Generic CPI does not establish constant-consumption energy-price outturns or
an energy-specific forecast. Open [issue #2526](https://github.com/PolicyEngine/policyengine-uk/issues/2526)
tracks energy-specific index alignment and a sourced future assumption.

See [dataset sources](../../../../docs/engineering/skills/dataset-sources.md)
for the declaration and migration contract. Existing metadata-free private
Microcosm files stay flat until a producer or caller supplies a verified
declaration; this consumer change does not label released artifacts.

The additional indices have their own source limits:

| Stored input | Variable index | Source coverage and terminal behavior |
|---|---|---|
| Salary-sacrifice pension contributions | `indices.obr.average_earnings` | Earnings growth has source values through 2073; its cumulative index compounds through 2039. |
| Water and sewerage charges | `indices.ofwat.water_bills` | Raw growth ends in 2029 at 4.5%; that rate carries into later years when the cumulative index is generated, through 2039. |
| Housing service charges | `indices.obr.lagged_average_earnings` | Lagged growth is generated through 2074 from the preceding year's earnings; its cumulative index compounds through 2039. |
| Rail usage | `gov.dft.rail.ridership_index` | The source cumulative index ends in 2029 at 1.044. Its terminal level stays flat, so the projection ratio is one in 2031 and 2032. |

The `indices.*` paths in this table are relative to
`gov.economic_assumptions`. Source dates remain distinct from the later dates
added by fiscal-year conversion.


## How the 2031+ values were constructed

Issue [#1379](https://github.com/PolicyEngine/policyengine-uk/issues/1379)
flagged that the year-by-year 2031+ values weren't documented. They are
constructed as follows:

- **CPI** is pinned to the Bank of England's 2.0% target from 2031-01-01
  onwards.
- **RPI** and **CPIH** use the stored convergence assumptions: 2.30% in
  2031 and 2.37% in 2032, reaching 2.39% in 2035 and then holding that rate
  through 2073. Their annual steps are not uniform. The 0.39 pp gap above
  CPI is the OBR's published
  long-run wedge to account for housing-cost growth ([long-run difference
  between RPI and CPI inflation][rpi-cpi]).
- **Average earnings** use 3.32% in 2031 and 3.71% in 2032, reaching 3.83%
  in 2036 and then holding that rate through 2073. These are existing model
  convergence assumptions beyond the EFO forecast horizon.
- **`road_fuel_volume`** is held flat at 0% after the OBR forecast ends —
  i.e. the final EFO forecast volume is held constant in real terms.

Review these stored assumptions when refreshing the EFO or long-run sources.
They are not annual EFO forecasts for 2031 onwards. The 2031–2032 rates
directly affect projections through the dataset horizon.

## Statutory uprating inputs

[`statutory_uprating_inputs/`](./statutory_uprating_inputs/) holds the two
published statistics that set the April uprating of the State Pension:
September CPI (ONS D7G7) and May-July average weekly earnings total pay
growth (ONS KAC3). They are keyed to their observation month, not to
1 January, and carry `preserve_calendar_dates`.

Each series holds published figures and then a null. From there,
[`create_statutory_uprating_inputs.py`](./create_statutory_uprating_inputs.py)
fills in calendar-year growth from `yoy_growth.obr` plus `forecast_gap`, the
OBR's statutory-basis forecast minus the calendar-year growth stored here, so
the baseline input equals the OBR's figure.
The gap is zero after the EFO horizon, so the forecasts fall back to
calendar-year growth. A scenario that edits calendar-year growth therefore
moves them, and a scenario can also set them directly.

After each release, add the new published figure in place of the null and
move the null one year on: September CPI in October, May-July earnings in
September. Then replace May-July earnings with the October release's figure,
which the review uses: the April 2025 and April 2026 rises used October's
4.1% and 4.8%, where September's first estimates were 4.0% and 4.7%.

## September CPI uprating

[`create_september_cpi_uprating.py`](./create_september_cpi_uprating.py)
builds `yoy_growth.september_cpi_uprating`, the rise taking effect in April
of each year (keyed to 1 January, like the other series), from
`statutory_uprating_inputs.cpi_september`: September CPI of the year before,
rounded to the published 0.1 percentage points, and zero when prices did not
rise. `create_economic_assumption_indices` compounds it into
`indices.september_cpi_uprating`. The triple lock reads the same rounded
September figure, so a scenario that edits calendar-year CPI or sets
September CPI directly moves both.

Most benefits rise each April by this measure: the Secretary of State's
annual review under Social Security Administration Act 1992 s150 measures
prices by the CPI 12-month rate for the previous September (every Up-rating
Order Explanatory Memorandum since April 2011; 3.8% for April 2026, written
statement HCWS1101). `gov.benefit_uprating_cpi`, which the benefit rate
parameters name as their `uprating`, follows `indices.september_cpi_uprating`,
and so do the Universal Credit standard allowance and health element indices
built from it. Housing Benefit non-dependant deduction income bands, DfE
funding rates, the Childcare Offer for Wales hourly rate and the council tax
high value surcharge follow the lagged calendar-year CPI projection through
`indices.obr.lagged_cpi`, pending their own uprating models. The deduction amounts continue to follow September CPI.
The savings credit threshold and Housing
Benefit pension-age allowances are within the s150 review, under
[s150(1)(l) and (h)](https://www.legislation.gov.uk/ukpga/1992/5/section/150),
even though their increases in practice are linked to earnings rather than
September CPI.

## Pension Credit earnings uprating

[`create_earnings_uprating.py`](./create_earnings_uprating.py) builds
`yoy_growth.earnings_uprating` from the previous May-July total-pay AWE input
used by the triple lock, rounded to the published 0.1 percentage points.
`indices.earnings_uprating` compounds it without rounding the index levels,
so rounding cannot push the increase below earnings. When earnings fall,
the projection holds amounts unchanged.

The Pension Credit standard minimum guarantee and the three lower Housing
Benefit pension-age personal allowances, which equal it, use this index after
their last published amounts. [SSAA 1992 s150A(1)(d) and (2)](https://www.legislation.gov.uk/ukpga/1992/5/section/150A)
require the guarantee to rise at least with earnings; they impose no CPI or
2.5% floor. This projection uses that earnings minimum, allowing published
amounts to reflect discretionary increases. For April 2027, May-July 2026
earnings growth of 3.9% gives £238 × 1.039 = £247.282 a week for a single
person and £363.25 × 1.039 = £377.41675 for a couple, before benefit rounding.

The Savings Credit maximum rises by September CPI, as stated in
[HCWS1101](https://questions-statements.parliament.uk/written-statements/detail/2025-11-26/hcws1101).
After general uprating, the projected threshold is derived as the standard
minimum guarantee minus the maximum divided by the phase-in rate (60%).
Published thresholds keep their own rounding. The 2026-27 maxima are £17.96
and £20.10, from the [DWP rates table](https://www.gov.uk/government/publications/benefit-and-pension-rates-2026-to-2027/proposed-benefit-and-pension-rates-2026-to-2027#pension-credit).
A zero phase-in rate pays no Savings Credit, so that year keeps the threshold
in force before it.

The three higher Housing Benefit pension-age personal allowances, for those
who reached State Pension age before April 2021, are the standard minimum
guarantee plus the maximum Savings Credit
([HB A3/2021](https://www.gov.uk/government/publications/housing-benefit-adjudication-circulars-2021/a32021-housing-benefit-person-who-have-attained-the-qualifying-age-for-state-pension-credit-amendment-regulations-2021),
paragraphs 3-5); each published amount from 2019-20 to 2026-27 is that sum
rounded up to the next 5p.
[`../dwp/housing_benefit/allowances/create_pension_age_allowances.py`](../dwp/housing_benefit/allowances/create_pension_age_allowances.py)
derives the years after the published amounts as that sum, after general
uprating, so each part keeps its own index. For April 2027 that is
£247.282 + £17.96 × 1.035 = £265.8706 a week for a single person or lone
parent and £377.41675 + £20.10 × 1.035 = £398.22025 for a couple.

Income Tax Act 2007 ss21 and 57 index the basic rate limit and the personal
allowance by this measure once no freeze applies.
[`../hmrc/create_threshold_indexation.py`](../hmrc/create_threshold_indexation.py)
applies them from 2031-32, keeps the primary threshold, upper earnings limit
and Class 4 profits limits aligned with them, and raises the secondary
threshold by the same rises, up to the last year of
`indices.september_cpi_uprating`.

## Refreshing after a new EFO

1. Replace the 2025-2030 block in each series with values from the new EFO
   detailed forecast tables (note the EFO release month in the header comment).
   The importer converts annual economy growth percentages to decimal rates
   and rounds them to four decimal places. Review the economy-series diff
   deliberately when running a full CLI import: with the real March 2026
   economy workbook, the existing extraction changes cumulative 2030 indices
   relative to the stored series by RPI −0.0880%, CPI −0.0584%, average
   earnings −0.0585% and house prices +0.0194%. Receipts-only rendering can
   reproduce the committed YAML byte for byte; a full import also refreshes
   these economy series.
2. Recompute the 2031-2073 convergence path so the first long-run year
   continues smoothly from the new last forecast year (no jump). If the new
   EFO forecasts a year that a series has no entry for, add that entry first:
   the importer only replaces existing entries, and stops naming the series
   and year it cannot update.
3. Nothing needs regenerating: `create_economic_assumption_indices` rebuilds
   the cumulative `indices` parameters from these series whenever the
   tax-benefit system processes its parameters (`tax_benefit_system.py`).
4. Update the EFO reference in each series' `metadata.reference`.
5. Regenerate `statutory_uprating_inputs/forecast_gap/` from the same EFO.
   `policyengine_uk/utils/import_obr_forecasts.py` does this when it updates
   `yoy_growth.yaml`; pass the receipts tables with `--receipts-file` or
   `--receipts-url` so September CPI uses the OBR's September forecast. If
   you edit `yoy_growth.yaml` by hand instead, rerun it with `--gaps-only`.
6. Refresh the receipts series (`stamp_duty_land_tax.*`,
   `business_rates.*`). The importer does this in the same run when it also
   gets the receipts tables of the EFO whose outturn year is one earlier
   (March 2025 for March 2026), with `--previous-receipts-file` or
   `--previous-receipts-url`; their outturn is the base for the outturn
   year's growth. It finds each line by table title and row label, so table
   renumbering does not matter, and reads only that table's rows. It takes
   each workbook's release from its contents sheet, or else its file name or
   URL, and refuses receipts tables from another EFO or of unknown release.
   Every selected table in both releases must declare `£ billion` in its
   header (`£bn` and `£ bn` are also accepted, ignoring case and whitespace).
   Other units, including `£m`, and missing or ambiguous declarations stop
   the import before any file is written, so different cash magnitudes
   cannot be combined across releases.
   Then update the published levels in
   `policyengine_uk/tests/test_corporate_receipts_statistics.py`
   (`OBR_RECEIPTS_BN`), which pin the series to the OBR's tables. Pass
   `--skip-receipts-growth` only to leave them on the previous EFO.
7. If the new EFO runs past `PROJECTION_END_YEAR`, move it on (see
   [Dataset projection horizon](#dataset-projection-horizon)).

For example, for March 2026:

```bash
uv run python -m policyengine_uk.utils.import_obr_forecasts \
  --file economy_tables_march_2026.xlsx \
  --receipts-file receipts_tables_march_2026.xlsx \
  --previous-receipts-file receipts_tables_march_2025.xlsx
```

The EFO refresh does not touch `finance_ni.domestic_rates`; OBR does not
publish a Northern Ireland domestic rates bill series (see below).

For `obr.council_tax`, take each country's growth in receipts from
Expenditure Table 4.1, not its "council tax level" row: dataset projection
divides the receipts growth by the growth in household weights itself
(#2067). When a forecast year becomes an outturn, replace it with the growth
in the published liability the comments in `yoy_growth.yaml` name, and add the
figures to `PUBLISHED_OUTTURNS` in
`policyengine_uk/tests/test_council_tax_uprating.py`.

## Northern Ireland domestic rates

`finance_ni.domestic_rates` is the growth in the average Northern Ireland
domestic rates bill: the combined regional and district domestic poundage
across the 11 councils, each council weighted by its domestic rates paid in
the previous year. It is a national average, so it does not reproduce any one
council's bill or changes in reliefs. The comments in
[`yoy_growth.yaml`](./yoy_growth.yaml) give the derivation and
`policyengine_uk/tests/test_domestic_rates_uprating.py` recomputes it from the
published figures. To refresh it each spring:

1. Add the new year's domestic district and regional poundages for every
   council from the Department of Finance
   [rate poundages](https://www.finance-ni.gov.uk/articles/rate-poundages)
   tables, and the latest year of Land & Property Services' domestic rates
   collected by district council, to the tables in that test. The years it
   checks follow from those tables: published years must match the
   recomputed growth, and later years must equal the last published year's.
2. Set the new year's value to the recomputed growth, rounded to 4 decimals,
   and the projected years after it to the same value (or change the
   projection rule and its test together).
3. Revisit that projection against the regional rate Order and any agreed
   Northern Ireland Budget, and keep it labelled as an assumption. Run the
   test file.

[rpi-cpi]: https://obr.uk/box/the-long-run-difference-between-rpi-and-cpi-inflation/
