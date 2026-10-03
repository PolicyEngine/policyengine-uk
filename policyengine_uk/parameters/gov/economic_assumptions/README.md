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

## Refreshing after a new EFO

1. Replace the 2025-2030 block in each series with values from the new EFO
   detailed forecast tables (note the EFO release month in the header comment).
2. Recompute the 2031-2073 convergence path so the first long-run year
   continues smoothly from the new last forecast year (no jump).
3. Nothing needs regenerating: `create_economic_assumption_indices` rebuilds
   the cumulative `indices` parameters from these series whenever the
   tax-benefit system processes its parameters (`tax_benefit_system.py`).
4. Update the EFO reference in each series' `metadata.reference`.

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
