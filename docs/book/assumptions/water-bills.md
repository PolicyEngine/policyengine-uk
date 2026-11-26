# Water bills projection and uprating

This documentation describes the water bills projection and uprating methodology used in PolicyEngine UK.

## Overview

`gov.economic_assumptions.yoy_growth.ofwat.water_bills` is nominal growth in the average household water and sewerage bill in England and Wales. Each year is the charging year starting in April, so 2025 is 2025-26. `policyengine_uk/utils/water/forecast_water_bills.py` derives the values that are not published outturn, and `policyengine_uk/tests/test_water_bills_growth.py` checks the stored values against it.

## Growth rates

| Year | Growth rate | Source |
|------|-------------|--------|
| 2022 | 5.2% | Ofwat average bills, real bills converted to nominal with CPIH |
| 2023 | 9.2% | As above |
| 2024 | 4.4% | As above |
| 2025 | 27% | [Ofwat statement, 29 January 2026](https://www.ofwat.gov.uk/ofwat-responds-to-water-sector-average-bill-figures/) (later figure; Ofwat's [30 January 2025 statement](https://www.ofwat.gov.uk/average-bills-2025-26-press-statement/) forecast 26%) |
| 2026 | 5.4% | [Water UK, 28 January 2026](https://www.water.org.uk/news-views-publications/news/record-investment-average-household-water-bills-rise-ps33-year-april): national average £639, up £33 |
| 2027 | 5.5% | Projection from the PR24 final determinations, below |
| 2028 | 5.0% | As above |
| 2029 | 4.9% | As above |

## Projection for 2027-28 to 2029-30

Ofwat's [PR24 final determinations](https://www.ofwat.gov.uk/wp-content/uploads/2024/12/PR24-FD-sector-summary-revised.pdf) (19 December 2024, sector summary page 21) set the average water and wastewater company bill at £440 in 2024-25 and £597 in 2029-30, before inflation: real growth of 597 / 440 = 1.3568 over five years. The table is committed as `policyengine_uk/utils/water/pr24_final_determination_bills.csv`.

1. Real growth already realised: the published 2025-26 and 2026-27 nominal increases less CPIH, 1.27 / 1.0327 × 1.054 / 1.0388 = 1.2478.
2. Real growth left: 1.3568 / 1.2478 = 1.0874, spread evenly over three years, 2.83% a year.
3. Inflation added back from `yoy_growth.obr.cpih` (the OBR's October 2026 forecast). Ofwat indexes bills to CPIH in the November before the charging year, so charging year t takes calendar year t-1: 1.0283 × 1.0324 = 6.2% for 2027-28, × 1.0330 = 6.2% for 2028-29, × 1.0214 = 5.0% for 2029-30.

```{note}
Open assumptions:

- The final determinations publish only the 2024-25 and 2029-30 averages, so the even real profile over the last three years is an assumption.
- The Competition and Markets Authority redetermined five companies' price controls in March 2026, and Ofwat's 2026 cost change determinations may add to some bills. Neither is reflected here.
- The 2025-26 and 2026-27 figures come from Ofwat's and Water UK's own averages, which may not use exactly the same weights as the final determination average.
```

After any change to these values, rerun `policyengine_uk/utils/create_ahc_deflator.py`: the after housing costs CPI removes water charges, and `policyengine_uk/tests/test_ahc_deflator.py` fails until its stored values are updated.

## Scotland and Northern Ireland

Ofwat's bills cover England and Wales. When a dataset is projected forward, each household's `water_and_sewerage_charges` grows by its own country's series (`uprate_water_and_sewerage_charges` in `policyengine_uk/data/economic_assumptions.py`):

- England and Wales, and households with an unknown region, take `ofwat.water_bills`.
- Scotland takes `scottish_water.water_bills`. Scottish Water sets household charges within limits from the [Water Industry Commission for Scotland](https://wics.scot/) (WICS), and every council tax band's charge is a fixed fraction of Band D, so each band rises by the same percentage.
- Northern Ireland has no domestic water charges, so any charge a dataset gives its households is held flat.

This holds to the end of the dataset projection (2032). After it, policyengine-core grows every household's charge by the index the variable declares, Ofwat's England and Wales series, as it did before this split.

| Year | Scottish Water growth | Source |
|------|-------------|--------|
| 2022 | 4.2% | [WICS, charges scheme 2022-23](https://wics.scot/publications/price-setting/strategic-review-charges-2021-27/scottish-waters-charges-scheme/charges-scheme-2022-23) |
| 2023 | 5.0% | [WICS, charges scheme 2023-24](https://wics.scot/publications/price-setting/strategic-review-charges-2021-27/scottish-waters-charges-scheme/charges-scheme-2023-24) |
| 2024 | 8.8% | [WICS, charges scheme 2024-25](https://wics.scot/publications/price-setting/strategic-review-charges-2021-27/scottish-waters-charges-scheme/charges-scheme-2024-25) |
| 2025 | 9.9% | [Scottish Water, 28 January 2025](https://www.scottishwater.co.uk/About-Us/News-and-Views/2025/01/Charges-2025-to-2026-Announcement) |
| 2026 | 8.67% | [Scottish Water, 22 January 2026](https://www.scottishwater.co.uk/about-us/news-and-views/2026/01/230126-charges-2026) |
| 2027 | 5.7% | Final Determination central projection: CPI forecast 3.2% plus 2.5 percentage points |
| 2028 | 4.6% | CPI forecast 2.1% plus 2.5 percentage points |
| 2029 | 4.4% | CPI forecast 1.9% plus 2.5 percentage points |
| 2030 | 4.5% | CPI forecast 2.0% plus 0.5 points core and 2.0 points conditional WCB allowance |
| 2031 | 4.5% | As above |
| 2032 | 4.5% | As above |

Each year is the charging year starting in April, so 2027 is 2027-28. The 2027-2032 values project the central profile in WICS's [Final Determination for 2027-33](https://www.wics.scot/system/files/2026-11/Final-Determination-2027-33-main-document.pdf#page=389) (12 November 2026; Tables 163-164 and section 9.6.1/Table 171, PDF pages 389-390 and 394). The price-inflation forecast is 3.2%, 2.1%, 1.9%, 2.0%, 2.0% and 2.0%; the charge measure uses October CPI in the previous year for 2027-28, then September CPI in the previous year from 2028-29.

The projection follows WICS's central assumption that Scottish Water meets the West Central Bioresources conditions. For 2030-2032, the unconditional real cap is 0.5%, with a further 2.0% conditional on those conditions being met; the projection includes that allowance. It excludes the separate 0.3% conditional allowance for uncertain costs, which WICS also leaves out of its central revenue modelling. These values describe a projected cap profile, not announced annual charges. The core cap applies cumulatively, so Scottish Water can vary the annual profile within it. Replace each projection with the announced increase when available.

`policyengine_uk/utils/create_ahc_deflator.py` still reads the England and Wales index. It is a standalone script that the model does not run.
