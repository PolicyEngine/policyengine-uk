# Water bills projection and uprating

This documentation describes the water bills projection and uprating methodology used in PolicyEngine UK.

## Overview

```{note}
We implement water bills projections through a combination of historical data analysis and regulatory projection data.
```

The system uses:

1. **Historical data** (2021-2025) from Ofwat average bills
2. **Regulatory projection data** from Ofwat company-specific increases (2025-2030)
3. **Economic uprating** using Consumer Price Index (CPIH) growth rates

## Implementation

### Data sources

#### Historical data
The projection uses historical real water bills data from Ofwat:
- **2021**: £486 (real terms)
- **2022**: £470 (real terms)  
- **2023**: £486 (real terms)
- **2024**: £492 (real terms)
- **2025**: £503 (real terms)

**Data source**: [Ofwat average bills data for England and Wales](https://www.ofwat.gov.uk/average-bills-press-statement-2024-25/)

#### Regulatory projections
```{important}
We source company-specific water bill increases from the Consumer Council for Water (CCW) based on Ofwat's price review data for 2025-2030. The data includes projected bills for 16 water companies covering both water and sewerage services.
```

**Data source**: [CCW Water Company Bill Increases 2025-30](https://www.ccw.org.uk/our-work/price-review/how-much-will-my-water-and-sewerage-bills-increase-by-2030/breakdown-of-water-companies-bill-increases-2025-30/)

### Projection methodology
 
#### Historical period (2021-2025)
1. We convert real bills to nominal terms using CPIH values
2. We calculate year-on-year nominal growth rates
3. We normalize to 2021 baseline (index = 100)

#### Future period (2025-2030)
1. We calculate average of company-specific projected increases
2. We apply Consumer Price Index (CPIH) uprating to account for inflation
3. We compound inflation adjustments year-over-year

```{tip}
The methodology ensures we preserve real increases from regulatory decisions, apply additional inflation adjustments using CPIH forecasts, and account for both policy changes and economic conditions in future projections.
```

### Code structure

#### Core implementation
- **Location**: `policyengine_uk/utils/water/forecast_water_bills.py`
- **Function**: `project_water_bills()`
- **Data**: `policyengine_uk/utils/water/ofwat_increases.csv`

#### Parameters integration
We store water bills year-on-year growth rates in:
- **Location**: `policyengine_uk/parameters/gov/economic_assumptions/yoy_growth.yaml`
- **Parameter**: `ofwat.water_bills`

### Growth rates

The model uses these year-on-year growth rates. Each year is the charging year starting in April, so 2025 is 2025-26.

| Year | Growth rate | Source |
|------|-------------|--------|
| 2022 | 5.2% | Ofwat average bills, real bills converted to nominal with CPIH |
| 2023 | 9.2% | As above |
| 2024 | 4.4% | As above |
| 2025 | 27% | [Ofwat statement, 29 January 2026](https://www.ofwat.gov.uk/ofwat-responds-to-water-sector-average-bill-figures/) (later figure; Ofwat's [30 January 2025 statement](https://www.ofwat.gov.uk/average-bills-2025-26-press-statement/) forecast 26%) |
| 2026 | 5.4% | [Water UK, 28 January 2026](https://www.water.org.uk/news-views-publications/news/record-investment-average-household-water-bills-rise-ps33-year-april): national average £639, up £33 |
| 2027 | 4.6% | Projection from `forecast_water_bills.py` |
| 2028 | 4.5% | As above |
| 2029 | 4.5% | As above |

```{warning}
The 2027-2029 projections cannot be reproduced from the repository. They take the CCW table, which reflects Ofwat's PR24 *draft* determinations rather than the final ones, weight each company by customer numbers, and add a hardcoded CPIH path. The customer weights were in `ofwat_increases.csv`, which is gitignored and was never committed.
```

## Scotland and Northern Ireland

Ofwat's bills cover England and Wales. When a dataset is projected forward, each household's `water_and_sewerage_charges` grows by its own country's series (`uprate_water_and_sewerage_charges` in `policyengine_uk/data/economic_assumptions.py`):

- England and Wales, and households with an unknown region, take `ofwat.water_bills`.
- Scotland takes `scottish_water.water_bills`. Scottish Water sets household charges within limits from the [Water Industry Commission for Scotland](https://wics.scot/) (WICS), and every council tax band's charge is a fixed fraction of Band D, so each band rises by the same percentage.
- Northern Ireland has no domestic water charges, so any charge a dataset gives its households is held flat.

| Year | Scottish Water growth | Source |
|------|-------------|--------|
| 2022 | 4.2% | [WICS, charges scheme 2022-23](https://wics.scot/publications/price-setting/strategic-review-charges-2021-27/scottish-waters-charges-scheme/charges-scheme-2022-23) |
| 2023 | 5.0% | [WICS, charges scheme 2023-24](https://wics.scot/publications/price-setting/strategic-review-charges-2021-27/scottish-waters-charges-scheme/charges-scheme-2023-24) |
| 2024 | 8.8% | [WICS, charges scheme 2024-25](https://wics.scot/publications/price-setting/strategic-review-charges-2021-27/scottish-waters-charges-scheme/charges-scheme-2024-25) |
| 2025 | 9.9% | [Scottish Water, 28 January 2025](https://www.scottishwater.co.uk/About-Us/News-and-Views/2025/01/Charges-2025-to-2026-Announcement) |
| 2026 | 8.67% | [Scottish Water, 22 January 2026](https://www.scottishwater.co.uk/about-us/news-and-views/2026/01/230126-charges-2026) |
| 2027 | 3.9% | WICS Draft Determination 2027-33: CPI + 2%, with WICS's CPI assumption of 1.9% |
| 2028 | 3.9% | As above |
| 2029 | 4.1% | As above, with CPI at 2.1% |

Each year is the charging year starting in April, so 2025 is 2025-26. Later years hold the 2029-30 rate. [WICS publishes its Final Determination for 2027-33](https://wics.scot/latest/wics-publishes-2027-33-draft-determination) on 29 October 2026; the 2027-2029 values should then be replaced with it.

`policyengine_uk/utils/create_ahc_deflator.py` still reads the England and Wales index. It is a standalone script that the model does not run.
