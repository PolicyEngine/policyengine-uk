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

The model uses these resulting year-on-year growth rates:

| Year | Growth rate |
|------|-------------|
| 2022 | 5.2% |
| 2023 | 9.2% |
| 2024 | 4.4% |
| 2025 | 6.1% |
| 2026 | 6.1% |
| 2027 | 5.1% |
| 2028 | 3.8% |
| 2029 | 4.3% |

### Scotland and Northern Ireland

The Ofwat series covers England and Wales only. The dataset projection uprates `water_and_sewerage_charges` by country (`uprate_water_charges` in `policyengine_uk/data/economic_assumptions.py`):

- England and Wales take `ofwat.water_bills`.
- Scotland takes `scottish_water.water_bills`, the published rise in Scottish Water's household charges: 1.8% (2021-22), 4.2%, 5%, 8.8%, 9.9% and 8.67% (2026-27). From 2027-28 it assumes 4% a year: CPI (the OBR's 2.0%) plus 2%, the cap in the Water Industry Commission for Scotland's draft determination for 2027-33. The final determination is due on 29 October 2026.
- Northern Ireland has no domestic water charges, so any charge a dataset gives its households is held flat.

The variable has no `uprating` attribute, so like council tax it is held at its last projected value after the projection horizon.
