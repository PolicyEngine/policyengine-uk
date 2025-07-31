# Universal Credit rebalancing reforms

```{note}
The Universal Credit rebalancing reforms represent changes to Universal Credit provisions introduced through the Universal Credit Bill. These reforms take effect from April 2026 and are designed to adjust benefit levels and eligibility criteria.
```

## Overview

```{important}
The reforms consist of two main components: health element changes for new claimants and standard allowance uplifts.
```

1. **Health element changes for new claimants**: New Universal Credit claimants from April 2026 onwards receive a fixed health element amount, while existing claimants continue to receive inflation-linked increases.

2. **Standard allowance uplifts**: The standard allowance receives additional uplifts beyond the annual inflationary increase from 2026-2029.

## Health element changes

From April 2026, new Universal Credit claimants who qualify for the Limited Capacity for Work-Related Activity (LCWRA) element receive a fixed monthly amount of £217.26, rather than the inflation-adjusted amount that pre-2026 claimants continue to receive.

The implementation uses transition probabilities based on WPI Economics analysis for the Trussell Trust, derived from administrative Personal Independence Payment data. The probability of being a new claimant varies by year:

- 2026: 11%
- 2027: 13%
- 2028: 16%
- 2029: 22%

## Standard allowance uplifts

The standard allowance receives additional percentage uplifts beyond the normal inflationary increase:

- 2026: 2.3% additional uplift
- 2027: 3.1% additional uplift (cumulative)
- 2028: 4.0% additional uplift (cumulative)
- 2029: 4.8% additional uplift (cumulative)

These uplifts are applied to the previous year's standard allowance amount and compound over time.

## Implementation

```{tip}
The reforms are implemented through parameters, scenario modifiers, and scenarios that work together to enable policy analysis.
```

- **Parameters**: Three YAML files define the reform's activation status, health element amount for new claimants, and standard allowance uplift rates.
- **Scenario modifier**: The `add_universal_credit_reform` function applies the changes to Universal Credit calculations during microsimulation.
- **Scenario**: The `universal_credit_july_2025_reform` scenario enables the reforms in policy analysis.

## Examples

You can use these reforms in your own analysis by creating a `Simulation` with parametric changes to modify the reform parameters.

### Disabling the rebalancing reforms entirely

```python
from policyengine_uk import Simulation, Scenario

# Disable the reforms from 2026 onwards
scenario = Scenario(parameter_changes={
    "gov.dwp.universal_credit.rebalancing.active": False,
})

sim = Simulation(scenario=scenario)
```

### Changing the standard allowance uplift parameters

```python
from policyengine_uk import Simulation, Scenario

# Set different uplift rates - e.g. 5% in 2026, 7% in 2027
scenario = Scenario(parameter_changes={
    "gov.dwp.universal_credit.rebalancing.standard_allowance_uplift": {
        "2026-01-01": 0.05,
        "2027-01-01": 0.07,
        "2028-01-01": 0.07,
        "2029-01-01": 0.07
    }
})

sim = Simulation(scenario=scenario)
```

### Changing the health element amount for new claimants

```python
from policyengine_uk import Simulation, Scenario

# Set the new claimant health element to £250 per month
scenario = Scenario(parameter_changes={
    "gov.dwp.universal_credit.rebalancing.new_claimant_health_element": {
        "2026-01-01": 250.00
    }
})

sim = Simulation(scenario=scenario)
```

## Legislative reference

The reforms are based on provisions in the Universal Credit Bill, available at: https://bills.parliament.uk/publications/62123/documents/6889.