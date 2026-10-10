# Universal Credit rebalancing reforms

```{note}
The Universal Credit rebalancing reforms represent changes to Universal Credit provisions introduced through the Universal Credit Bill. These reforms take effect from April 2026 and are designed to adjust benefit levels and eligibility criteria.
```

## Overview

```{important}
The reforms combine a higher standard allowance, protected awards for existing health-element recipients, and a lower fixed health element for most new claimants.
```

1. **Protected awards for existing claimants**: Existing recipients of the health element keep the combined value of their standard allowance and health element at least in line with CPI inflation through 2029-30.

2. **Health element changes for new claimants**: New Universal Credit claimants from April 2026 onwards receive a fixed monthly health element amount of £217.26, rather than the protected existing-claimant amount.

3. **Standard allowance uplifts**: The standard allowance receives additional uplifts beyond the annual inflationary increase from 2026-2029.

## Health element changes

From April 2026, new Universal Credit claimants who qualify for the Limited Capability for Work-Related Activity (LCWRA) element receive a fixed monthly amount of £217.26.

Existing recipients are treated differently. Their LCWRA amount is uprated so that the combined value of:

- their standard allowance, and
- their health element

rises at least in line with CPI inflation. The model implements that protection through the health element itself, preserving the combined award outcome without separately modelling the small administrative split between protected LCWRA amounts and any under-25 standard allowance supplement.

The implementation uses transition probabilities based on WPI Economics analysis for the Trussell Trust, derived from administrative Personal Independence Payment data. The probability of being a new claimant varies by year:

- 2026: 11%
- 2027: 13%
- 2028: 16%
- 2029: 22%

## Standard allowance uplifts

Universal Credit Act 2025 s. 1 sets the minimum standard allowance for 2026-27 to 2029-30. Each year's minimum is the previous year's CPI-uprated amount (the 2025-26 amount for 2026-27), increased by September CPI (never below 0%), and then by that year's uplift:

- 2026-27: 2.3%
- 2027-28: 3.1%
- 2028-29: 4.0%
- 2029-30: 4.8%

Each uplift is measured against the CPI-only path from 2025-26, not compounded on the previous one, so from one year to the next the allowance grows by CPI times (1 + this year's uplift) / (1 + last year's uplift). After 2029-30 the uplift stays at 4.8% and the allowance grows with CPI alone.

The 2026-27 amounts are the legislated rates in `standard_allowance/amount.yaml`. Later years are uprated by `gov.dwp.universal_credit.standard_allowance.uprating`, the benefit uprating CPI index times (1 + the year's uplift), which `rebalancing/create_standard_allowance_uprating.py` builds when parameters are processed. A legislated rate for one of these years includes that year's statutory uplift; if the uplift in force differs, through a reform or with `rebalancing.active` false (no uplift), the rate is rescaled by (1 + uplift in force) / (1 + statutory uplift).

## Implementation

```{tip}
The reforms are implemented through parameters, scenario modifiers, and scenarios that work together to enable policy analysis.
```

- **Parameters**: Three YAML files define the reform's activation status, health element amount for new claimants, and standard allowance uplift rates. The uplift reaches the standard allowance through its uprating index.
- **Scenario modifier**: The `add_universal_credit_reform` function applies the protected existing-claimant health-element path during microsimulation.
- **Scenario**: The `universal_credit_july_2025_reform` scenario enables the reforms in policy analysis.

## Examples

You can use these reforms in your own analysis by creating a `Simulation` with parametric changes to modify the reform parameters.

### Disabling the rebalancing reforms entirely

```python
from policyengine_uk import Simulation, Scenario

# Disable the reforms from 2026 onwards
scenario = Scenario(
    parameter_changes={
        "gov.dwp.universal_credit.rebalancing.active": False,
    }
)

sim = Simulation(scenario=scenario)
```

### Changing the standard allowance uplift parameters

```python
from policyengine_uk import Simulation, Scenario

# Set different uplift rates - e.g. 5% in 2026-27, 7% from 2027-28.
# A bare year names the fiscal year from 6 April.
scenario = Scenario(
    parameter_changes={
        "gov.dwp.universal_credit.rebalancing.standard_allowance_uplift": {
            "2026": 0.05,
            "2027": 0.07,
            "2028": 0.07,
            "2029": 0.07,
        }
    }
)

sim = Simulation(scenario=scenario)
```

The uplift reaches the allowance through parameter processing, which `Scenario(parameter_changes=...)` re-runs. A `reform=` dictionary is applied after processing, so to change the allowance that way set `gov.dwp.universal_credit.standard_allowance.amount` directly.

### Changing the health element amount for new claimants

```python
from policyengine_uk import Simulation, Scenario

# Set the new claimant health element to £250 per month
scenario = Scenario(
    parameter_changes={
        "gov.dwp.universal_credit.rebalancing.new_claimant_health_element": {
            "2026-01-01": 250.00
        }
    }
)

sim = Simulation(scenario=scenario)
```

## Legislative reference

The reforms are based on the Universal Credit Act 2025, the Bill and its impact assessment:

- https://www.legislation.gov.uk/ukpga/2025/22/section/1
- https://bills.parliament.uk/publications/62123/documents/6889
- https://bills.parliament.uk/publications/62124/documents/6892
- https://assets.publishing.service.gov.uk/media/689ca49e1c63de6de5bb1298/withdrawn-universal-credit-bill-uc-rebalancing-impact-assessment.pdf
