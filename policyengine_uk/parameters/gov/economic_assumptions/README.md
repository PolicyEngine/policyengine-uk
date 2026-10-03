# Economic assumptions

Year-on-year growth series for the UK economy used to uprate parameters and
calibrate the input dataset. The single source of truth is
[`yoy_growth.yaml`](./yoy_growth.yaml); downstream cumulative indices are
generated from it by
[`create_economic_assumption_indices.py`](./create_economic_assumption_indices.py).

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

## Time horizons

Three horizons are stitched together for each series:

1. **Outturn** (history through 2024): ONS published data, copied from OBR
   detailed forecast tables.
2. **EFO forecast** (2025-2030): latest OBR Economic and Fiscal Outlook
   supplementary tables. The version currently checked in is **March 2026**;
   refresh after each new EFO.
3. **Long-run equilibrium** (2031-2073): constructed from OBR's long-run
   assumptions (Fiscal Risks and Sustainability report) and the long-run
   RPI-CPI wedge methodology.

## How the 2031+ values were constructed

Issue [#1379](https://github.com/PolicyEngine/policyengine-uk/issues/1379)
flagged that the year-by-year 2031+ values weren't documented. They are
constructed as follows:

- **CPI** is pinned to the Bank of England's 2.0% target from 2031-01-01
  onwards.
- **RPI** and **CPIH** linearly interpolate from the final EFO value
  (2030-01-01) up to a 2.39% steady state by 2035-01-01, then hold flat
  through 2073-01-01. The 0.39 pp gap above CPI is the OBR's published
  long-run wedge to account for housing-cost growth ([long-run difference
  between RPI and CPI inflation][rpi-cpi]).
- **Average earnings** linearly interpolate from the final EFO value
  (2030-01-01) up to a 3.83% steady state by 2036-01-01, then hold flat.
  This is consistent with the OBR's long-run productivity assumption
  (1.8%) added to CPI (2.0%).
- **`road_fuel_volume`** is held flat at 0% after the OBR forecast ends —
  i.e. the final EFO forecast volume is held constant in real terms.

These steady-state assumptions are reviewed each time the OBR publishes a
new Fiscal Risks and Sustainability report. The convergence path itself
is conservative interpolation and is not load-bearing for short-horizon
analysis.

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

## Refreshing after a new EFO

1. Replace the 2025-2030 block in each series with values from the new EFO
   detailed forecast tables (note the EFO release month in the header comment).
2. Recompute the 2031-2073 convergence path so the first long-run year
   continues smoothly from the new last forecast year (no jump).
3. Run `python policyengine_uk/parameters/gov/economic_assumptions/create_economic_assumption_indices.py`
   to regenerate the cumulative `indices/` parameters that uprating depends
   on.
4. Update the EFO reference in each series' `metadata.reference`.
5. Regenerate `statutory_uprating_inputs/forecast_gap/` from the same EFO.
   `policyengine_uk/utils/import_obr_forecasts.py` does this when it updates
   `yoy_growth.yaml`; pass the receipts tables with `--receipts-file` or
   `--receipts-url` so September CPI uses the OBR's September forecast. If
   you edit `yoy_growth.yaml` by hand instead, rerun it with `--gaps-only`.

[rpi-cpi]: https://obr.uk/box/the-long-run-difference-between-rpi-and-cpi-inflation/
