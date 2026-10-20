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

Two parameters hold this amount, and both are uprated by `gov.economic_assumptions.indices.uc_health_element`, so they follow the same path:

- `gov.dwp.universal_credit.elements.disabled.amount` is the LCWRA element the `uc_LCWRA_element` formula pays. For an inactive year processed by the rebalancing scenario, the scenario replaces that paid amount with the pre-Act counterfactual described below. From 2033-34, after the data's projection ends, the rebalancing scenario no longer sets the element and the formula reads this parameter.
- `gov.dwp.universal_credit.rebalancing.new_claimant_health_element` is the amount the rebalancing scenario pays new claimants in the years it sets the element, `uc_reform.REBALANCING_YEARS` (2026-27 to 2032-33).

A change to the freeze or to the benefit uprating index moves both, and so does a reform that sets the index, `gov.economic_assumptions.indices.uc_health_element`, directly (it replaces the freeze and the no-fall floor for the years it names). A reform to either amount itself does not change the other.

`rebalancing/create_health_element_uprating.py` builds the index when parameters are processed: the benefit uprating index, held flat in each year in which `rebalancing.health_element_freeze` and `rebalancing.active` are both true.

Existing recipients are treated differently. Universal Credit Regulations 2013 reg. 36 gives one amount, the protected LCWRA amount, to every pre-2026 claimant, severe conditions criteria claimant or terminally ill claimant, whatever their age or couple status. For 2026-27 it is £429.80 a month ([SI 2026/113](https://www.legislation.gov.uk/uksi/2026/113/made) reg. 3(3)(b)), stored in `gov.dwp.universal_credit.rebalancing.protected_health_element`.

For a tax year without a legislated amount, the model uses the lowest amount the Universal Credit Act 2025 s. 4 duty allows. For every standard allowance amount, the protected amount plus that allowance must be at least the previous year's sum, increased by the relevant CPI percentage: the CPI 12-month rate in the September before the tax year, never below 0% (s. 4(4)(a)). The model reads that rate from `gov.economic_assumptions.statutory_uprating_inputs.cpi_september`. Section 3 switches off the element's ordinary uprating, so the amount otherwise stays where it was. Run from the 2025-26 amounts at the 3.8% September 2025 CPI rate, this rule gives the legislated £429.80.

The s. 4 duty covers 2026-27 to 2029-30 only, and s. 3 disapplies the annual up-rating only in the tax years ending 5 April 2026 to 5 April 2029. The protected row stays in reg. 36: s. 2 only relabels it. So from 2030-31 the protected amount is the year before's amount uprated by the same index as the new-claimant amount, `gov.economic_assumptions.indices.uc_health_element`, and a protected claimant keeps the higher amount.

Whether a benefit unit gets the new-claimant rate is the benefit unit's `uc_receives_new_claimant_health_element` for the year. A household situation can set it, for example `{"uc_receives_new_claimant_health_element": {"2026": True}}` on the benefit unit; otherwise it is false, which pays the protected amount. A dataset can supply it too. A simulation built from data that does not supply it assigns it by a seeded draw against `gov.dwp.universal_credit.rebalancing.new_claimant_share`, from 2026-27 to the end of the data's projection. The shares to 2029-30 are WPI Economics' estimates for the Trussell Trust, derived from administrative Personal Independence Payment data:

- 2026: 11%
- 2027: 13%
- 2028: 16%
- 2029: 22%

Later years hold 22%. That is an assumption, not a source: the share keeps rising as the caseload turns over, so holding it understates new claimants from 2030-31.

## Standard allowance uplifts

Universal Credit Act 2025 s. 1 sets the minimum standard allowance for 2026-27 to 2029-30. Each year's minimum is the previous year's CPI-uprated amount (the 2025-26 amount for 2026-27), increased by September CPI (never below 0%), and then by that year's uplift:

- 2026-27: 2.3%
- 2027-28: 3.1%
- 2028-29: 4.0%
- 2029-30: 4.8%

The model projects future inflation using `gov.benefit_uprating_cpi`, its benefit uprating index, rather than a separate September CPI series for the standard allowance.

Each uplift is measured against the CPI-only path from 2025-26, not compounded on the previous one, so from one year to the next the allowance grows by CPI times (1 + this year's uplift) / (1 + last year's uplift). After 2029-30 the uplift stays at 4.8% and the allowance grows with CPI alone.

The 2026-27 amounts are the legislated rates in `standard_allowance/amount.yaml`, used as they are. Later years are uprated by `gov.economic_assumptions.indices.uc_standard_allowance`, which `rebalancing/create_standard_allowance_uprating.py` builds when parameters are processed: the benefit uprating CPI index times one plus the uplift. For a legislated year the uplift is the one its rates include (2.3% for 2026-27); for later years it is the uplift in force. So switching `rebalancing.active` off, or changing a later year's uplift, moves every year after 2026-27, which stays at its legislated rates. To change 2026-27 itself, set `gov.dwp.universal_credit.standard_allowance.amount`.

For a single claimant under 25, the legislated 2026-27 amount is £338.58, above the Act's £336.60 minimum (£316.98 increased by 3.8% CPI, then 2.3%, with rounding at each step). The projection carries that margin forward; dividing the legislated rate by 1.023 gives the projection's CPI-only base, rather than the Act's Step 2 minimum for that claimant type.

## Implementation

```{tip}
The reforms are implemented through parameters, scenario modifiers, and scenarios that work together to enable policy analysis.
```

- **Parameters**: YAML files define the reform's activation status, the health element amounts for new claimants and for protected (pre-2026) claimants, the health element freeze, and the standard allowance uplift rates. The uplift reaches the standard allowance through its uprating index.
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

For the health component, an inactive year uses the 2025-26 monthly LCWRA amount (£423.27), uprated by the model's ordinary benefit uprating index from 2025-26 to that year. It does not apply the new/protected claimant split, the health-element freeze or the protected-amount floor. Each inactive year starts independently from that pre-Act amount, so a mixed on/off schedule cannot feed an inactive award into the later protected calculation. Explicit LCWRA amount reforms and directly supplied element awards retain precedence. Applying an amount change through `Scenario.apply` also refreshes an already-calculated health element and final Universal Credit award. The underlying `elements.disabled.amount` parameter still holds the legislated new-claimant amount; this counterfactual changes the paid health element through the scenario. This is a health-component counterfactual, not validation that the toggle disables every provision of the Act.

The 2026-27 standard allowance stays at its legislated rates, which include the 2.3% uplift; from 2027-28 it follows CPI alone from the 2026-27 rates less that uplift.

### Changing the standard allowance uplift parameters

```python
from policyengine_uk import Simulation, Scenario

# Set different uplift rates from 2027-28 (2026-27 is legislated), e.g. 7%.
# A bare year names the fiscal year from 6 April.
scenario = Scenario(
    parameter_changes={
        "gov.dwp.universal_credit.rebalancing.standard_allowance_uplift": {
            "2027": 0.07,
            "2028": 0.07,
            "2029": 0.07,
        }
    }
)

sim = Simulation(scenario=scenario)
```

The uplift reaches the allowance through parameter processing. Both `Scenario(parameter_changes=...)` and a `reform=` dictionary keyed by fiscal year re-run that pipeline, including after parameters are reset and reprocessed. A bounded override of `standard_allowance.amount` uses the override as given during its period and restores the projected allowance afterwards.

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

The reforms are based on the Universal Credit Act 2025, the Bill and its impact assessment:

- https://www.legislation.gov.uk/ukpga/2025/22/section/1
- https://www.legislation.gov.uk/ukpga/2025/22/section/3
- https://bills.parliament.uk/publications/62123/documents/6889
- https://bills.parliament.uk/publications/62124/documents/6892
- https://assets.publishing.service.gov.uk/media/689ca49e1c63de6de5bb1298/withdrawn-universal-credit-bill-uc-rebalancing-impact-assessment.pdf
