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
| `national_living_wage`  | National living wage growth, for April of each year      | EFO economy Table 1.13  |
| `non_labour_income`     | Non-labour household income growth                       | derived from EFO        |
| `road_fuel_volume`      | Petrol + diesel road-fuel clearances                     | HMRC Hydrocarbon Oils + OBR fuel-duty forecast |
| `petrol_spending_litre_proxy` | Spending growth that preserves road-fuel litres    | HMRC + OBR              |
| `diesel_spending_litre_proxy` | Same, for diesel                                   | HMRC + OBR              |
| `finance_ni.domestic_rates` | Average Northern Ireland domestic rates bill (regional plus district poundage) | DoF rate poundages, LPS rates paid, NI draft Budget 2026-29 |
| `stamp_duty_land_tax.residential` | SDLT receipts from residential property          | EFO receipts, property transactions taxes by sector: Table 4.7 in October 2026 |
| `stamp_duty_land_tax.non_residential` | SDLT receipts from non-residential property  | EFO receipts, property transactions taxes by sector: Table 4.7 in October 2026 |
| `business_rates.great_britain` | Business rates receipts, England, Scotland and Wales (cash) | EFO receipts, current receipts (cash basis): Table 4.8 in October 2026 |
| `business_rates.northern_ireland` | Northern Ireland business rates receipts      | EFO receipts, other taxes: Table 4.2 in October 2026 |
| `gambling_duty_bases.<duty>` | The base of each of the seven betting and gaming duties (receipts over the model's rate) | HMRC Betting and Gaming tables (2024-25, 2025-26), then EFO receipts, betting and gaming duties forecast breakdown: Table 4.10 in October 2026 |

The four receipts series project the corporate SDLT and business rates
statistics (`gov.hmrc.stamp_duty.statistics`,
`gov.hmrc.business_rates.statistics`) from their latest outturn. Each is the
ratio of consecutive published receipts levels, to six decimals: outturn
growth for the EFO's outturn year (its outturn over the year before's outturn
in an earlier EFO), the EFO's forecast years, and after them the
`average_earnings` path. Years before the outturn year are kept, so each
index keeps its base year.

The seven `gambling_duty_bases` series (`general_betting`, `pool_betting`,
`remote_gaming`, `machine_games`, `gaming`, `bingo`, `lottery`) grow the
gambling duty inputs (#2738). They grow a duty's base, not its receipts:
each year's receipts divided by the rate the model charges that fiscal
year. The model then applies its own rate changes, such as Remote Gaming
Duty's rise from 21% to 40% on 1 April 2026, once. The table publishes
forecasts only, so each series starts from HMRC's 2024-25 receipts, the
model's base year, and its 2025-26 outturn, which the importer holds in
`RECEIPTS_SERIES_SPECS`. A year whose rate is zero, Bingo Duty's from
2026-27, holds the base flat. See
[gambling duties](../../../../docs/engineering/gambling-duties.md#projection)
for each duty's rates, the higher-stake share Machine Games Duty's rate
assumes, and the approximations.

`national_living_wage` projects the minimum wage rates
(`gov.hmrc.minimum_wage`) after the last rate set. It holds the growth of the
rates the Government has set, then of the OBR's estimates, both from the
national living wage table of the detailed economy tables (Table 1.13 in
October 2026), then `average_earnings`' long-run growth, year for year. HM
Treasury costed Budget 2026's Carer's Allowance taper on the OBR's estimates.
`utils/import_obr_forecasts.py` writes the series with the other economy
series. It finds the table by its title, reads the level under each year
across the table's one row of years, and writes each year's level over the
year before's, to six decimals. The table's note says up to which year the
Government has set the rate, and the importer writes those years and the
OBR's estimates under separate comments. The importer stops before writing
any file if the table declares a unit other than £ per hour, or lacks one row
of years and one row labelled "National Living Wage (NLW)". It also stops if
the years skip or repeat, if a year lacks a positive level, if a figure has no
year above it, or if the table lacks that note. `test_minimum_wage_projection.py`
holds the October 2026 table, checks it against the importer's fixture, and
fails if the series stops reproducing the table to the penny, or if its
long-run years stop matching `average_earnings`.

## Time horizons

Three horizons are stitched together for each OBR and ONS series (not
`finance_ni.domestic_rates`, which has its own method, below):

1. **Outturn** (history through 2025): ONS published data, copied from OBR
   detailed forecast tables.
2. **EFO forecast** (2026-2031): latest OBR Economic and Fiscal Outlook
   supplementary tables. The version currently checked in is **October
   2026**; refresh after each new EFO.
3. **Long-run equilibrium** (2032-2073): constructed from OBR's long-run
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
several series end with the EFO. Of those the projection uses, per-capita GDP
and mixed income, council tax, house prices and social and private rents end
in 2031, the October 2026 EFO's last year. Mortgage interest ends in 2030:
the OBR stops forecasting RPI mortgage interest payments after 2029, before
RPI changes method in February 2030. Northern Ireland domestic rates, which
have their own method (below), also end in 2030.
A parameter returns its latest value after its last date, so in 2032 the
first group holds its 2031 growth rate, and in 2031 and 2032 the second holds
its 2030 rate. That is an extrapolation, not an OBR forecast; replace it with
the next EFO's values once one covers those years.

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
use a separate declaration-aware projector, `uprate_energy`. Unlabelled
datasets retain their stored amounts through the projection horizon,
preserving legacy inputs that already use FY2026-27 prices. A dataset's
explicit `energy_price_basis` opts into the household energy price indices
(see [Household energy prices](#household-energy-prices)): electricity
spending moves with `energy_prices.*.electricity`, gas spending with
`energy_prices.*.gas` and combined spending with
`energy_prices.*.electricity_gas_and_solid_fuels`. The declaration covers
only these three inputs, independently of any other generic uprating
exclusions. They remain outside both the unconditional growth mapping and
fallback, so no second index grows them after 2030.

The declaration retains `calendar_year` or `fiscal_year` and its integer year,
and the projector reads the index of that kind: a `calendar_year` 2024 basis
reads the January to December 2024 level, a `fiscal_year` 2024 basis the
April 2024 to March 2025 level. The target is always the fiscal year index,
because model year Y is fiscal year Y–(Y+1). Both annual indices are dated
1 January of their first year. The projector applies `I[target year] /
I[declared price year]` to the supplied observation, so each projected year
is the observation times one ratio, not a chain of yearly ratios. A requested
declared projection raises an error if either 1 January precedes the selected
index's first stated value, or if the index has no values. Unlabelled inputs
and declarations with no stored energy inputs do not require index history.
Each projected child records its effective fiscal-year basis, while the
source observation keeps its original declaration. The variables' own
`uprating` names the same fiscal year indices, so Core's uprating of a
directly supplied amount after its last period agrees with the dataset
projection.

See [dataset sources](../../../../docs/engineering/skills/dataset-sources.md)
for the declaration and migration contract. Existing metadata-free private
Microcosm files stay flat until a producer or caller supplies a verified
declaration; this consumer change does not label released artifacts.

The additional indices have their own source limits:

| Stored input | Variable index | Source coverage and terminal behavior |
|---|---|---|
| Salary-sacrifice pension contributions | `indices.obr.average_earnings` | Earnings growth has source values through 2073; its cumulative index compounds through 2039. |
| Water and sewerage charges | `indices.ofwat.water_bills` | Raw growth ends in 2029 at 5.0%; that rate carries into later years when the cumulative index is generated, through 2039. |
| Housing service charges | `indices.obr.lagged_average_earnings` | Lagged growth is generated through 2074 from the preceding year's earnings; its cumulative index compounds through 2039. |
| Rail usage | `gov.dft.rail.ridership_index` | The source cumulative index ends in 2029 at 1.044. Its terminal level stays flat, so the projection ratio is one in 2031 and 2032. |

The `indices.*` paths in this table are relative to
`gov.economic_assumptions`. Source dates remain distinct from the later dates
added by fiscal-year conversion.


## How the 2032+ values were constructed

Issue [#1379](https://github.com/PolicyEngine/policyengine-uk/issues/1379)
flagged that the year-by-year long-run values weren't documented. Since the
October 2026 EFO they start in 2032 and are constructed as follows:

- **CPI** is at the Bank of England's 2.0% target in the EFO's 2031
  forecast and is held there from 2032-01-01 onwards.
- **RPI** and **CPIH** move in equal steps, rounded to four decimals, from
  the EFO's 2031 forecast of 2.18% to 2.39% in 2035: 2.23% in 2032, 2.29% in
  2033 and 2.34% in 2034. They then hold 2.39% through 2073. The 0.39 pp gap
  above CPI is the OBR's published long-run wedge to account for
  housing-cost growth ([long-run difference between RPI and CPI
  inflation][rpi-cpi]).
- **Average earnings** move the same way from the EFO's 2031 forecast of
  2.60% to 3.83% in 2036: 2.85% in 2032, 3.09% in 2033, 3.34% in 2034 and
  3.58% in 2035. They then hold 3.83% through 2073. The 3.83% rate is an
  existing model assumption, unchanged since the November 2025 EFO.
- **`road_fuel_volume`** is held flat at 0% after the OBR forecast ends —
  i.e. the final EFO forecast volume is held constant in real terms.

The equal steps replace the stored convergence rates that followed the March
2026 EFO, which would have taken earnings from 2.60% in 2031 to 3.71% in
2032. Review these assumptions when refreshing the EFO or the OBR's long-term
economic determinants. They are not annual EFO forecasts. The 2032 rates
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
`indices.obr.lagged_cpi`, pending their own uprating models. The deduction
amounts continue to follow September CPI. The savings credit threshold and
Housing Benefit pension-age allowances are within the s150 review, under
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

## Household energy prices

`energy_prices` holds the price indices that project household electricity
and gas spending (see [Dataset projection horizon](#dataset-projection-horizon)).
They price each fuel with VAT at the rate the energy inputs assume,
`gov.simulation.vat.energy_input_price_basis_rate` (5%). `domestic_energy_vat`
divides the inputs by one plus that rate and applies the rate in force, so an
index that included a VAT change would count it twice: once in spending and
again in the tax. Holding VAT at the basis rate takes out every change in VAT
on domestic electricity that the published prices include, the zero rate
from 1 October 2026 and its Budget 2026 extension among them, and a reform to
`gov.hmrc.vat` never moves the indices.

The other Budget 2026 measures that bear on energy bills stay in. The EFO
gives an inflation effect for the fuel duty changes and the VAT cut
(paragraph 3.10), and none for abolishing the carbon price support or funding
lower contracts for difference levies. It says those measures "are intended
to offset the increase in electricity bills" that the British Industrial
Competitiveness Scheme brings consumers outside energy-intensive industry
(paragraph 3.19).

### Inputs

| Parameter | Contents | Source |
|---|---|---|
| `ons` | Monthly CPI indices, 2015 = 100, from January 2015: electricity (D7DT), gas (D7DU) and electricity, gas and solid fuels (DK9U, classes 04.5.1, 04.5.2 and 04.5.4); their annual CPI weights (CJXA, CJXB, A9F4); and, as node metadata, `last_full_quarter`, the last quarter ONS publishes all three months of in every series | ONS MM23 |
| `obr.utilities` | CPI utilities (electricity and gas) inflation, year on year, by quarter, from the first quarter ONS has not published in full | EFO economy tables, CPI category inflation (Table 1.19 in October 2026) |
| `consumption_shares` | Each calendar quarter's share of a year's domestic electricity and of domestic gas consumption, the mean over the complete years from 2015 | DESNZ Energy Trends ET 5.2 and ET 4.1 |
| `embedded_electricity_vat` | The VAT rate on domestic electricity that the published prices and forecast include, in Great Britain and in Northern Ireland, and Northern Ireland's share of UK domestic electricity consumption (2.69% in 2024), which weights them | SI 2026/987, Budget 2026 and its policy costings, EFO paragraph 3.10, DESNZ subnational consumption statistics |
| `held_flat` | Whether the annual indices hold the previous year's level | `no_economic_assumptions` sets it |

`policyengine_uk/utils/import_energy_prices.py` writes the first three;
maintainers edit the last two by hand. `embedded_electricity_vat` describes the
source data, not policy: it follows the VAT the ONS prices include and the
OBR assumed, which a reform to `gov.hmrc.vat` does not change.

### Method

`create_energy_price_indices.py`, a generation step that runs whenever
policyengine-uk processes the parameters, builds three series for each of
`electricity`, `gas` and `electricity_gas_and_solid_fuels`:

- `quarterly`, 2015Q1 to 2042Q1. To `last_full_quarter` (2026Q3 in the
  October 2026 inputs), the mean of the monthly
  index, each month over the VAT factor its price includes,
  `1 + s × ((1 + r) / (1 + b) − 1)`. Here `r` is the UK rate on domestic
  electricity in the published price on the 15th of the month (the mean of
  the Great Britain and Northern Ireland rates, weighting each by its
  consumption), `b` the basis
  rate and `s` electricity's share of the series' CPI weight: 1 for
  electricity, 0 for gas and CJXA / A9F4 for the combined series. After that,
  the level a year earlier times one plus the OBR's utilities inflation net
  of the change in electricity VAT, `(1 + g) × u(q − 4) / u(q) − 1`, where
  `u` is the same factor for electricity's share of utilities,
  CJXA / (CJXA + CJXB), as the mean over the quarter's months. After the OBR's
  last quarter (2032Q1), its last rate holds.
- `calendar_year`, January to December, and `fiscal_year`, April to March,
  2015 to 2041, each at 1 January of its first year. Each averages the
  year's four quarterly levels, weighting each by its share of the year's
  consumption; the combined series weights the electricity and gas shares by
  their CPI weights.

Where `held_flat` is true for a year, both annual series take the previous
year's level. `no_economic_assumptions` sets it from its first input year as
it zeroes the growth series, and since it is a raw input, every later rebuild
of the indices keeps it.

The generator reads every input at the month or quarter it applies to, not
at its stated dates, so a reform can state one value for a year or a span of
quarters: `{"gov.economic_assumptions.energy_prices.obr.utilities": {"2027":
0.1}}` sets utilities inflation to 10% in each quarter of 2027 (through
Core's `Reform.from_dict` a bare year applies from that year onward).
`Parameter.update` with a start and no end removes the stated values after
the start, and its value then sets every month or quarter after it. The
generator reads the ONS prices only to the end of `last_full_quarter` and
`obr.utilities` only after it, and a reform cannot move that boundary. A month or quarter with no value,
such as one a reform sets to `None`, stops generation. A forecast quarter
grows from the level a year earlier, so a reform to the ONS prices also moves
the forecast levels, though not their growth.

### Limits

- The OBR forecasts utilities only, so after the ONS outturn electricity and
  gas grow at the same rate: each index is its fuel's own price to there and
  a utilities proxy after it. The combined series includes solid fuels in its
  outturn and not in its forecast.
- The indices are prices, so a projection holds each household's consumption
  fixed.
- The seasonal shares are fixed averages, not each year's, and Northern
  Ireland's share of consumption stays at 2024's. The share matters only
  while the two VAT rates differ, October 2026 to March 2027.
- The OBR's rates are year on year, so each forecast quarter rests on the
  level four quarters before it.

## Refreshing after a new EFO

1. Replace the forecast block in each series with values from the new EFO
   detailed forecast tables (note the EFO release month in the header comment).
   An autumn EFO also revises the calendar year before its release, now
   outturn (October 2026 revised 2025), and forecasts six years after it; the
   importer's defaults cover only six years from the release year, so pass
   `--forecast-start-year` and `--forecast-years` (2025 and 7 for October
   2026).
   The importer converts annual economy growth percentages to decimal rates
   and rounds them to four decimal places. Review the economy-series diff
   deliberately when running a full CLI import: with the real March 2026
   economy workbook, the existing extraction changes cumulative 2030 indices
   relative to the stored series by RPI −0.0880%, CPI −0.0584%, average
   earnings −0.0585% and house prices +0.0194%. Receipts-only rendering can
   reproduce the committed YAML byte for byte; a full import also refreshes
   these economy series.
2. Recompute the long-run convergence path so the first long-run year
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
   The same run refreshes the `gambling_duty_bases` series from the new
   EFO's betting and gaming duties forecast breakdown. They read no previous
   EFO: the year before the table's first comes from HMRC's receipts in each
   spec. When the table starts a year later (2027-28 in October 2027), add
   HMRC's outturn for the year before from its latest Betting and Gaming
   tables; the importer stops and names the year until you do. Check the
   EFO's policy tables for any new measure in the betting and gaming lines.
   Then update the published levels in
   `policyengine_uk/tests/test_gambling_duty_base_projection.py`.
7. The same run refreshes `national_living_wage` from the new economy
   tables' national living wage table (Table 1.13 in October 2026), with
   `average_earnings` after it. Then replace the cut-down table in
   `policyengine_uk/tests/fixtures/obr_economy/` (see its README) and the
   levels in `OBR_NATIONAL_LIVING_WAGE` in
   `policyengine_uk/tests/test_minimum_wage_projection.py`. Pass
   `--skip-national-living-wage` only to leave the series on the previous
   EFO.
8. If the new EFO runs past `PROJECTION_END_YEAR`, move it on (see
   [Dataset projection horizon](#dataset-projection-horizon)).
9. Refresh the household energy price inputs (see
   [Household energy prices](#household-energy-prices)) from the new EFO's
   economy tables, the MM23 release of the same month and the latest Energy
   Trends tables. The importer records the last quarter ONS publishes in
   full as `last_full_quarter`, takes the OBR forecast from the quarter after
   it, and stops before writing anything if an MM23 series has a gap or a
   year without its CPI weight, if the series come from different releases or
   if Table 1.19 has no quarter after the ONS outturn. Then check
   `embedded_electricity_vat.yaml` against the VAT on domestic electricity
   the EFO assumes. Replace the cut-down sources in
   `policyengine_uk/tests/fixtures/energy_prices/` and their SHA-256s, and
   update the outturn quarter and the hand-computed 2027Q1 and 2028Q3 checks
   in `policyengine_uk/tests/test_energy_price_indices.py`.

   ```bash
   uv run python -m policyengine_uk.utils.import_energy_prices \
     --mm23 mm23.csv \
     --obr-economy efo-october-2026-detailed-forecast-tables-economy.xlsx \
     --electricity-trends ET_5.2_SEP_26.xlsx \
     --gas-trends ET_4.1_SEP_26.xlsx
   ```

For example, for March 2026:

```bash
uv run python -m policyengine_uk.utils.import_obr_forecasts \
  --file economy_tables_march_2026.xlsx \
  --receipts-file receipts_tables_march_2026.xlsx \
  --previous-receipts-file receipts_tables_march_2025.xlsx
```

and for October 2026, whose receipts tables are numbered 4.x:

```bash
uv run python -m policyengine_uk.utils.import_obr_forecasts \
  --file efo-october-2026-detailed-forecast-tables-economy.xlsx \
  --receipts-file efo-october-2026-detailed-forecast-tables-receipts.xlsx \
  --previous-receipts-file policyengine_uk/tests/fixtures/obr_receipts/obr_efo_march_2026_receipts.xlsx \
  --forecast-start-year 2025 --forecast-years 7
```

The October 2026 import also needed, by hand: 2031 entries added to
`house_prices` and `rent` before the run, the 2032+ joins above, and the
series the importer does not cover (population, per-capita GDP, mixed and
non-labour income, household interest income, rail journeys per person,
council tax, social and private rents, the AHC deflator, Ofwat water bills,
road fuel volumes and the litre proxies, and the fuel duty RPI path in
`gov.hmrc.fuel_duty`). Each series' comments name its source and method.
The rail fare indices (`gov.dft.rail.fare_index` and `prior_law_fare_index`),
Bank Rate (`gov.boe.base_rate`, economy Table 1.9) and households' financial
assets (`household.wealth.financial_assets`, Table 1.11) also take October
2026 values.

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
