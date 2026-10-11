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

Existing recipients are treated differently. Universal Credit Regulations 2013 reg. 36 gives one amount, the protected LCWRA amount, to every pre-2026 claimant, severe conditions criteria claimant or terminally ill claimant, whatever their age or couple status. For 2026-27 it is £429.80 a month ([SI 2026/113](https://www.legislation.gov.uk/uksi/2026/113/made) reg. 3(3)(b)), stored in `gov.dwp.universal_credit.rebalancing.protected_health_element`.

For a tax year without a legislated amount, the model uses the lowest amount the Universal Credit Act 2025 s. 4 duty allows. For every standard allowance amount, the protected amount plus that allowance must be at least the previous year's sum, increased by the relevant CPI percentage: the CPI 12-month rate in the September before the tax year, never below 0% (s. 4(4)(a)). The model reads that rate from `gov.economic_assumptions.statutory_uprating_inputs.cpi_september`. Section 3 switches off the element's ordinary uprating, so the amount otherwise stays where it was. Run from the 2025-26 amounts at the 3.8% September 2025 CPI rate, this rule gives the legislated £429.80.

Whether a benefit unit gets the new-claimant rate is the benefit unit's `uc_receives_new_claimant_health_element` for the year. A household situation can set it, for example `{"uc_receives_new_claimant_health_element": {"2026": True}}` on the benefit unit; otherwise it is false, which pays the protected amount. A dataset can supply it too. A simulation built from data that does not supply it assigns it by a seeded draw, using transition probabilities based on WPI Economics analysis for the Trussell Trust, derived from administrative Personal Independence Payment data. The probability of being a new claimant varies by year:

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

These uplifts are applied to the CPI-uprated standard allowance for each year. In other words, the model first applies the usual CPI uprating and then applies the rebalancing uplift on top.

## Implementation

```{tip}
The reforms are implemented through parameters, scenario modifiers, and scenarios that work together to enable policy analysis.
```

- **Parameters**: YAML files define the reform's activation status, the health element amounts for new claimants and for protected (pre-2026) claimants, and the standard allowance uplift rates.
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

# Set different uplift rates - e.g. 5% in 2026, 7% in 2027
scenario = Scenario(
    parameter_changes={
        "gov.dwp.universal_credit.rebalancing.standard_allowance_uplift": {
            "2026-01-01": 0.05,
            "2027-01-01": 0.07,
            "2028-01-01": 0.07,
            "2029-01-01": 0.07,
        }
    }
)

sim = Simulation(scenario=scenario)
```

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

The reforms are based on the Universal Credit Bill and its impact assessment:

- https://bills.parliament.uk/publications/62123/documents/6889
- https://bills.parliament.uk/publications/62124/documents/6892
- https://assets.publishing.service.gov.uk/media/689ca49e1c63de6de5bb1298/withdrawn-universal-credit-bill-uc-rebalancing-impact-assessment.pdf
