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

Universal Credit Act 2025 s. 3 freezes the element for 2026-27 to 2029-30: it disapplies the annual up-rating in Social Security Administration Act 1992 s. 150(1) and (2) in the tax years ending 5 April 2026 to 5 April 2029, and an up-rating order takes effect from the tax year after the one in which it is made. The new-claimant amount therefore stays at £217.26 a month to 2029-30. From 2030-31 it is uprated from £217.26 by the benefit uprating index, one year's growth at a time. It never falls, because s. 150(2) provides only for increases; other Universal Credit amounts follow the benefit uprating index directly, which gives the same result whenever the index rises.

Two parameters hold this amount, and both are uprated by `gov.dwp.universal_credit.elements.disabled.uprating`, so they follow the same path:

- `gov.dwp.universal_credit.elements.disabled.amount` is the LCWRA element the `uc_LCWRA_element` formula pays. A simulation uses it from 2030-31, and whenever the rebalancing reforms are inactive.
- `gov.dwp.universal_credit.rebalancing.new_claimant_health_element` is the amount the rebalancing scenario pays new claimants for 2026-27 to 2029-30.

A change to the freeze or to the benefit uprating index moves both. A reform to either amount itself does not change the other.

`rebalancing/create_health_element_uprating.py` builds the index when parameters are processed: the benefit uprating index, held flat in each year in which `rebalancing.health_element_freeze` and `rebalancing.active` are both true.

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

- **Parameters**: YAML files define the reform's activation status, the health element amounts for new claimants and for protected (pre-2026) claimants, the health element freeze, and the standard allowance uplift rates.
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

# Set the new claimant health element to £250 per month from April 2026.
# A "start.stop" key sets the value over those dates. A single date such as
# "2026-01-01" would change that one day only and leave every year unchanged.
scenario = Scenario(
    parameter_changes={
        "gov.dwp.universal_credit.rebalancing.new_claimant_health_element": {
            "2026-04-06.2100-12-31": 250.00
        }
    }
)

sim = Simulation(scenario=scenario)
```

### Lifting the health element freeze

```python
from policyengine_uk import Simulation, Scenario

# Uprate the LCWRA element by CPI from 2028-29 instead of freezing it.
# A bare year names the fiscal year from 6 April.
scenario = Scenario(
    parameter_changes={
        "gov.dwp.universal_credit.rebalancing.health_element_freeze": {
            "2028": False,
            "2029": False,
        }
    }
)

sim = Simulation(scenario=scenario)
```

New claimants then get the uprated amount in 2028-29 and 2029-30, and every later year starts from that higher amount. The protected amount for existing claimants does not change; it follows the s. 4 floor.

The freeze reaches the element through parameter processing. A `Scenario(parameter_changes=...)` change and a `reform=` dictionary keyed by year (`reform={"gov.dwp.universal_credit.rebalancing.health_element_freeze": {"2028": False, "2029": False}}`) both re-run it, before the rebalancing scenario sets the 2026-27 to 2029-30 health elements. A `reform=` key naming a single day edits the annualised parameter on that day only and does not.

## Legislative reference

The reforms are based on the Universal Credit Bill and its impact assessment:

- https://www.legislation.gov.uk/ukpga/2025/22/section/3
- https://bills.parliament.uk/publications/62123/documents/6889
- https://bills.parliament.uk/publications/62124/documents/6892
- https://assets.publishing.service.gov.uk/media/689ca49e1c63de6de5bb1298/withdrawn-universal-credit-bill-uc-rebalancing-impact-assessment.pdf
