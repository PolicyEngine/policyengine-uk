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
| `consumer_price_index_ahc` | CPI excluding rents/maintenance/water (AHC measure)   | ONS adhoc 2863          |
| `rpi`                   | Retail Price Index year-on-year growth                   | EFO Table 1.7           |
| `average_earnings`      | Average weekly earnings growth                           | EFO Table 1.6           |
| `non_labour_income`     | Non-labour household income growth                       | derived from EFO        |
| `road_fuel_volume`      | Petrol + diesel road-fuel clearances                     | HMRC Hydrocarbon Oils + OBR fuel-duty forecast |
| `petrol_spending_litre_proxy` | Spending growth that preserves road-fuel litres    | HMRC + OBR              |
| `diesel_spending_litre_proxy` | Same, for diesel                                   | HMRC + OBR              |
| `finance_ni.domestic_rates` | Average Northern Ireland domestic rates bill (regional plus district poundage) | DoF rate poundages, LPS rates paid, NI draft Budget 2026-29 |

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
are deliberately excluded from this fallback as well as the annual growth
mapping. Their stored amounts already use FY2026-27 unit prices, so dataset
projection holds them flat, as documented in `uprating_indices.yaml`.

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
2. Recompute the 2031-2073 convergence path so the first long-run year
   continues smoothly from the new last forecast year (no jump).
3. Nothing needs regenerating: `create_economic_assumption_indices` rebuilds
   the cumulative `indices` parameters from these series whenever the
   tax-benefit system processes its parameters (`tax_benefit_system.py`).
4. Update the EFO reference in each series' `metadata.reference`.
5. Regenerate `statutory_uprating_inputs/forecast_gap/` from the same EFO.
   `policyengine_uk/utils/import_obr_forecasts.py` does this when it updates
   `yoy_growth.yaml`; pass the receipts tables with `--receipts-file` or
   `--receipts-url` so September CPI uses the OBR's September forecast. If
   you edit `yoy_growth.yaml` by hand instead, rerun it with `--gaps-only`.
6. If the new EFO runs past `PROJECTION_END_YEAR`, move it on (see
   [Dataset projection horizon](#dataset-projection-horizon)).

The EFO refresh does not touch `finance_ni.domestic_rates`; OBR does not
publish a Northern Ireland domestic rates bill series (see below).

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
