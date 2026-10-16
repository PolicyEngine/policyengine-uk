# Creating policy scenarios

The `Scenario` class lets you define policy reforms and apply them to simulations. This guide shows you how to create everything from simple parameter changes to complex reform packages, and how to combine different policy ideas together.

## Your first policy scenario

Let's start by creating a scenario that reduces the basic rate of income tax from 20% to 15%:

```python
from policyengine_uk import Scenario, Simulation

# Create a scenario with one policy change
scenario = Scenario(parameter_changes={"gov.hmrc.income_tax.rates.uk[0].rate": 0.15})

# Apply it to a simulation
situation = {
    "people": {"person": {"age": {2025: 35}, "employment_income": {2025: 40_000}}},
    "benunits": {"benunit": {"members": ["person"]}},
    "households": {"household": {"members": ["person"]}},
}

sim = Simulation(situation=situation, scenario=scenario)
income_tax = sim.calculate("income_tax", 2025).mean()
print(f"Income tax under 15% basic rate: £{income_tax:.2f}")
```

Under this scenario, this person would pay £2,486 instead of the current £4,486 - a reduction of £2,000 per year due to the lower tax rate.

```{note}
Scenarios apply policy changes without modifying your original simulation, allowing easy comparison between different policy options.
```

## Understanding parameter paths

PolicyEngine UK organises policy parameters in a hierarchical structure. Each parameter has a path that describes where it sits in the system:

```python
# Income tax parameters
"gov.hmrc.income_tax.rates.uk[0].rate"  # Basic rate (20%)

"gov.hmrc.income_tax.rates.uk[1].rate"  # Higher rate (40%)
"gov.hmrc.income_tax.personal_allowance"  # Personal allowance
"gov.hmrc.income_tax.rates.uk[0].threshold"  # Basic rate threshold

# Universal Credit parameters
"gov.dwp.universal_credit.standard_allowance.single.OVER_25"  # Single person allowance
"gov.dwp.universal_credit.elements.housing.max_monthly_cap"  # Housing cost cap
"gov.dwp.universal_credit.means_test.income_disregard"  # Work allowance

# Child benefits
"gov.hmrc.child_benefit.rates.first_child"  # First child rate
"gov.hmrc.child_benefit.rates.additional_child"  # Additional children rate
```

```{tip}
You can find parameter paths by exploring the PolicyEngine web app or looking in the `parameters/` directory of the codebase.
```

## Creating comprehensive reform packages

Real policy proposals often involve multiple changes. Here's how to create a comprehensive reform:

```{important}
This represents the kind of coordinated policy change you might see in a budget - real reforms often involve multiple interacting changes.
```

```python
# A comprehensive package that increases Universal Credit support while adjusting income tax
welfare_reform = Scenario(
    parameter_changes={
        # Increase UC standard allowances
        "gov.dwp.universal_credit.standard_allowance.single.OVER_25": 500,
        "gov.dwp.universal_credit.standard_allowance.single.UNDER_25": 400,
        "gov.dwp.universal_credit.standard_allowance.couple": 700,
        # Reduce UC taper rate (less benefit withdrawn per pound earned)
        "gov.dwp.universal_credit.means_test.reduction_rate": 0.55,
        # Increase income tax personal allowance
        "gov.hmrc.income_tax.personal_allowance": 15_000,
        # Reduce basic rate slightly to help fund UC increases
        "gov.hmrc.income_tax.rates.uk[0].rate": 0.22,
    }
)

# Test on a working family
family_situation = {
    "people": {
        "parent": {"age": {2025: 30}, "employment_income": {2025: 20_000}},
        "child": {"age": {2025: 5}},
    },
    "benunits": {"family": {"members": ["parent", "child"]}},
    "households": {
        "home": {
            "members": ["parent", "child"],
            "housing_costs": {2025: 7200},  # Annual housing costs
        }
    },
}

reformed_sim = Simulation(situation=family_situation, scenario=welfare_reform)

# Calculate the impact of this comprehensive package on the family
uc_amount = reformed_sim.calculate("universal_credit", 2025).mean()
income_tax = reformed_sim.calculate("income_tax", 2025).mean()
net_income = reformed_sim.calculate("household_net_income", 2025).mean()

print(f"Universal Credit: £{uc_amount:.2f} per month")
print(f"Income tax: £{income_tax:.2f} per year")
print(f"Monthly net income: £{net_income / 12:.2f}")
```

## Combining scenarios

```{tip}
You can combine different scenarios using the `+` operator, which is useful for testing different combinations of policies.
```

```python
# Create separate scenarios for different policy areas
tax_scenario = Scenario(
    parameter_changes={
        "gov.hmrc.income_tax.personal_allowance": 15_000,
        "gov.hmrc.income_tax.rates.uk[0].rate": 0.18,
    }
)

benefits_scenario = Scenario(
    parameter_changes={
        "gov.dwp.universal_credit.standard_allowance.single.OVER_25": 450,
        "gov.dwp.universal_credit.means_test.reduction_rate": 0.50,
    }
)

childcare_scenario = Scenario(
    parameter_changes={
        "gov.dwp.universal_credit.elements.childcare.max_proportion": 0.90
    }
)

# Combine them in different ways
tax_and_benefits = tax_scenario + benefits_scenario
full_package = tax_scenario + benefits_scenario + childcare_scenario

# Test each combination to see how different policy areas interact
# This shows how you can build up complex policies piece by piece
for name, scenario in [
    ("Tax only", tax_scenario),
    ("Benefits only", benefits_scenario),
    ("Tax + benefits", tax_and_benefits),
    ("Full package", full_package),
]:
    sim = Simulation(situation=family_situation, scenario=scenario)
    net_income = sim.calculate("household_net_income", 2025).mean()
    print(f"{name}: £{net_income / 12:.2f} per month")
```

A sum keeps the timing of each part's modifier. A simulation runs the modifiers of the parts set with `applied_before_data_load=True` before it builds its data, and the rest once the data is built, each in the order added. A sum with a part applied before data load applies all of its parameter changes first, before the data is built, with the precedence `+` gives them: changing the parameters rebuilds them, which would discard the edits of a modifier that has already run. The data's projected years then follow every parameter change of the sum. So `no_economic_assumptions + reform` freezes the data and the parameters and applies the reform, and a modifier that edits the data still runs once the data exists. Such a simulation builds its own copy of a `hf://` or `gs://` dataset rather than sharing the cached one, so its baseline and later simulations keep current law's projection. A sum reads `applied_before_data_load=True` only when every part that changes something is applied before data load. `Scenario.parts_by_data_load()` returns what is applied before data load and what is applied after. If you change a sum's `applied_before_data_load` or `simulation_modifier` to another value after making it, the whole sum is applied as one scenario, at the time its own `applied_before_data_load` says.

## Defining structural scenarios

Beyond simple parameter changes, you sometimes need scenarios that make structural modifications to how the tax-benefit system works. Let's walk through how to create these, using examples similar to those in PolicyEngine UK's scenarios module.

### Creating a two-child limit repeal scenario

The two-child limit restricts Universal Credit child elements to the first two children. Here's how to build a scenario that removes this restriction:

```{note}
The two-child limit is controlled by this parameter - setting it to infinity effectively removes the limit.
```

```python
import numpy as np
from policyengine_uk import Scenario

# The two-child limit is controlled by this parameter
# Setting it to infinity effectively removes the limit
repeal_two_child_limit = Scenario(
    parameter_changes={
        "gov.dwp.universal_credit.elements.child.limit.child_count": {
            "year:2026:10": np.inf  # From October 2026 onwards, no limit
        }
    }
)

# Test this on a family with three children
large_family = {
    "people": {
        "parent": {"age": {2026: 35}, "employment_income": {2026: 18_000}},
        "child1": {"age": {2026: 12}},
        "child2": {"age": {2026: 8}},
        "child3": {"age": {2026: 4}},  # Third child - currently gets no UC support
    },
    "benunits": {"family": {"members": ["parent", "child1", "child2", "child3"]}},
    "households": {
        "home": {
            "members": ["parent", "child1", "child2", "child3"],
            "housing_costs": {2026: 10200},  # Annual housing costs
        }
    },
}

# Compare the impact
baseline_sim = Simulation(situation=large_family)
reformed_sim = Simulation(situation=large_family, scenario=repeal_two_child_limit)

baseline_uc = baseline_sim.calculate("universal_credit", 2026).mean()
reformed_uc = reformed_sim.calculate("universal_credit", 2026).mean()

increase = reformed_uc - baseline_uc
print(f"UC increase from third child: £{increase:.2f} per month")
```

### Building a benefit cap reindexing scenario

```{warning}
The benefit cap hasn't risen with inflation since 2016.
```

Here's how to create a scenario that automatically indexes it to CPI:

```python
from policyengine_uk import Scenario, Simulation
from policyengine_core.parameters import Parameter


def reindex_benefit_cap_to_cpi(simulation: Simulation):
    """Modify simulation to index benefit cap parameters to CPI inflation"""
    # Reset the parameter system to make changes
    simulation.tax_benefit_system.reset_parameters()

    # Find all benefit cap parameters in the system
    params = (
        simulation.tax_benefit_system.parameters.gov.dwp.benefit_cap.get_descendants()
    )

    # Filter to only the actual parameter values (leaf nodes)
    cap_parameters = [param for param in params if isinstance(param, Parameter)]

    for parameter in cap_parameters:
        # Remove any values after 2025 (current frozen values)
        parameter.values_list = [
            entry for entry in parameter.values_list if entry.instant_str < "2026-01-01"
        ]

        # Set the parameter to follow CPI uprating from 2026
        parameter.metadata.update(uprating="gov.benefit_uprating_cpi")

    # Reprocess the parameters to apply changes
    simulation.tax_benefit_system.process_parameters()


# Create the scenario using a simulation modifier
reindex_benefit_cap = Scenario(simulation_modifier=reindex_benefit_cap_to_cpi)

# Test on a family that might hit the benefit cap
benefit_cap_family = {
    "people": {
        "parent1": {"age": {2026: 30}, "employment_income": {2026: 0}},
        "parent2": {"age": {2026: 28}, "employment_income": {2026: 0}},
        "child1": {"age": {2026: 6}},
        "child2": {"age": {2026: 3}},
    },
    "benunits": {"family": {"members": ["parent1", "parent2", "child1", "child2"]}},
    "households": {
        "home": {
            "members": ["parent1", "parent2", "child1", "child2"],
            "housing_costs": {2026: 14400},  # High annual housing costs
        }
    },
}

baseline_sim = Simulation(situation=benefit_cap_family)
reformed_sim = Simulation(situation=benefit_cap_family, scenario=reindex_benefit_cap)

# Compare the benefit cap levels
baseline_cap = baseline_sim.calculate("uc_benefit_cap", 2026).mean()
reformed_cap = reformed_sim.calculate("uc_benefit_cap", 2026).mean()

print(
    f"Benefit cap - frozen: £{baseline_cap:.0f}/year, indexed: £{reformed_cap:.0f}/year"
)
```

If you want to remove the cap entirely for a poverty-analysis package, PolicyEngine
UK also exposes a reusable scenario:

```python
from policyengine_uk import Simulation
from policyengine_uk.scenarios import abolish_benefit_cap

sim = Simulation(situation=benefit_cap_family, scenario=abolish_benefit_cap)
benefit_cap_reduction = sim.calculate("benefit_cap_reduction", 2026).mean()
print(f"Benefit cap reduction after abolition: £{benefit_cap_reduction:.0f}")
```

### Removing economic assumptions

If you want to isolate policy effects from forecast-driven uprating, use the
`no_economic_assumptions` scenario. It applies before data load, so it freezes
both parameter uprating and any dataset extension that depends on forecast
growth rates.

```python
from policyengine_uk import Simulation
from policyengine_uk.scenarios import no_economic_assumptions

situation = {
    "people": {"person": {"age": {2025: 40}, "employment_income": {2025: 30_000}}},
    "benunits": {"benunit": {"members": ["person"]}},
    "households": {"household": {"members": ["person"]}},
}

baseline = Simulation(situation=situation)
static = Simulation(situation=situation, scenario=no_economic_assumptions)

print(float(baseline.calculate("employment_income", 2026)[0]))
print(float(static.calculate("employment_income", 2026)[0]))
```

Add it to a reform to measure the reform without growth. The sum still applies the freeze before the data is built, so with a dataset (`Simulation(dataset=...)`) the projected years keep the first year's amounts too, and it applies the reform as usual:

```python
from policyengine_uk.model_api import Scenario

reform = Scenario.from_reform(
    {"gov.hmrc.income_tax.allowances.personal_allowance.amount": {"2025.2099": 20_000}}
)
static_reform = Simulation(
    situation=situation, scenario=no_economic_assumptions + reform
)
```

## Advanced scenario techniques

### Time-varying parameters

Some reforms phase in over time:

```{note}
A scenario that gradually increases the personal allowance over four years - this kind of phasing helps manage fiscal costs and economic adjustment.
```

```python
# A scenario that gradually increases the personal allowance over four years
# This kind of phasing helps manage fiscal costs and economic adjustment
phased_scenario = Scenario(
    parameter_changes={
        "gov.hmrc.income_tax.allowances.personal_allowance.amount": {
            "2025": 13_000,
            "2026": 14_000,
            "2027": 15_000,
            "2028": 16_000,
        }
    }
)

# Test this on a middle-income earner to see the progressive impact
situation = {
    "people": {"person": {"age": {2025: 30}, "employment_income": {2025: 35_000}}},
    "benunits": {"benunit": {"members": ["person"]}},
    "households": {"household": {"members": ["person"]}},
}

sim = Simulation(situation=situation, scenario=phased_scenario)

# Show how the tax burden decreases year by year
for year in [2025, 2026, 2027, 2028]:
    allowance = sim.calculate("income_tax_personal_allowance", year).mean()
    tax = sim.calculate("income_tax", year).mean()
    print(f"{year}: Personal allowance £{allowance:.0f}, annual tax £{tax:.2f}")
```

### Dated changes

Budgets date their measures: a rate from 6 April, a freeze extended to a later tax year, a change that ends. Every way of passing a reform writes its changes onto each parameter's statutory timeline, the dated values in the YAML files. That covers `Scenario(parameter_changes=...)`, `Simulation(reform=dict)`, `Scenario.from_reform` and policyengine-core's `Reform.from_dict`. The parameters are then processed as current law is:

- uprating and the income tax and NICs threshold indexation project each parameter forward;
- each parameter is annualised to UK fiscal years by its rule: its value on 30 April, or a day-weighted average over 6 April to 5 April for `fiscal_year_blend` parameters such as the CGT rates. Parameters marked `preserve_calendar_dates` keep their dates.

So a change from 6 April 2027 sets fiscal year 2027. A change to the personal allowance after 2030-31 moves the NICs thresholds aligned with it. A change to a CPI forecast moves everything uprated from it.

```python
from policyengine_uk import Simulation

rate = "gov.hmrc.income_tax.rates.uk[0].rate"
situation = {
    "people": {"person": {"age": {2027: 40}, "employment_income": {2027: 30_000}}},
    "benunits": {"benunit": {"members": ["person"]}},
    "households": {"household": {"members": ["person"]}},
}

# A basic rate of 21% from 6 April 2027 onwards.
from_april = Simulation(
    situation=situation, reform={rate: {"2027-04-06.2100-12-31": 0.21}}
)
# The same rate for 2027-28 only: 2028-29 is back to current law.
one_year = Simulation(
    situation=situation, reform={rate: {"2027-04-06.2028-04-05": 0.21}}
)
```

Outside a change's dates, prior law stays in force. Where the timeline states later values, they apply on their dates. Where it states none, prior law depends on how the parameter's future is made:

- the personal allowance and the basic rate limit are indexed from the previous tax year's amount (Income Tax Act 2007 ss21 and 57), so after a change ends indexation resumes from the changed amount. Freezing the allowance at £12,570 to 2033-34 gives £12,570 plus 2034-35's September CPI rise, rounded up to £10, for 2034-35, as the Finance Act 2021 freeze does for 2031-32. The National Insurance thresholds the model aligns with them follow: they align with the resumed path, and after a change to one of them alone they are aligned again;
- an amount uprated from an index, such as a benefit rate, returns to its uprated path: a one-year change to the UC standard allowance gives the uprated amount the next year. Whether a freeze of such an amount should instead resume from the frozen amount, as the 2016-2020 benefit freeze did, is an open question (policyengine-uk#2430).

A change "from a date onwards" is held flat to the end of 2100 and is not uprated or indexed. That is the key's literal reading, not something statute requires; to let indexation resume after a change, give its last tax year.

Each way of passing a reform reads period keys as it always has:

| Key | `reform=` dict | `parameter_changes` | `Reform.from_dict` |
|---|---|---|---|
| `"2027-04-06.2028-04-05"` | those dates | those dates | those dates |
| `"2027"` or `2027` | fiscal year 2027 only (calendar year 2027 on a calendar-year series) | fiscal year 2027 only (calendar year 2027 on a calendar-year series) | from 1 January 2027 onwards |
| `"2027-04-06"` | that one day of the annualised value | that one day | from that day onwards |
| a value with no period | from 1 January 2023 onwards | 2000 to 2099 | 2000 to 2099 |

A single-date key in a `reform=` dict overrides the annualised value on that day only. Formulas read annual values on 1 January, so `"2027-01-01"` sets fiscal year 2027 and `"2027-04-06"` changes nothing. On a calendar-year series (below), a 1 January key names that calendar year instead. The model logs a warning when a key can change nothing. Use `"start.stop"` keys for dated measures.

Some parameters hold one value per calendar year, dated 1 January, and are read there: the growth rates under `gov.economic_assumptions.yoy_growth`, the indices built from them under `gov.economic_assumptions.indices`, and the `household` parameters, which are not annualised. On these a bare year, or its 1 January, names the calendar year. So `{"gov.economic_assumptions.yoy_growth.obr.average_earnings": {"2027": 0.05}}` sets earnings growth in 2027: the 2027 earnings index, the May to July 2027 earnings input and the April 2028 triple lock all follow it.

Processing also builds some parameters from others: the triple lock rate (`gov.economic_assumptions.yoy_growth.triple_lock`), the lagged and private pension series, the September CPI uprating rate and the indices. A change to one is written as soon as it is built, so everything built from it follows. `{"gov.economic_assumptions.yoy_growth.triple_lock": {"2028": 0.05}}` uprates the State Pension by 5% in April 2028, exactly as `gov.dwp.state_pension.triple_lock.outturn` set for that April does. A change to an index uprates whatever is uprated by it. The deprecated `gov.simulation.labor_supply_responses` paths change the `labour_supply_responses` parameters they copy.

A dataset's later years are projected from its first by the economic assumptions as the simulation is built. Dated changes that change what that projection reads (a growth rate, say, through `parameter_changes`, `"start.stop"` or bare-year keys, or a 1 January key on a calendar-year series) are written before the data is built, so incomes, rents and council tax follow them, as with `applied_before_data_load=True`. Other dated changes come just after the data is built, before the steps that read parameters while the simulation is built: the Universal Credit rebalancing awards and the structural reforms that parameters switch on. Other single-day keys and a scenario's own simulation modifier run after those steps, as they always have, and leave the data as built. Datasets loaded from `hf://` or `gs://` are cached once projected, under current law only: a simulation whose projection inputs differ builds its own, so a scenario never reaches its baseline or a later simulation. A sum with a part applied before data load applies all its parameter changes before the data is built (see "Combining scenarios" above).

All of this applies when the scenario or reform is passed to `Simulation(...)`. `Scenario.apply(simulation)` on a simulation that is already built edits its annualised values instead, as it always has: a `"2027-04-06.2028-04-05"` key there overrides those dates of the fiscal-year values, so it does not set fiscal year 2027, and the model logs a warning saying so. Pass the scenario when constructing the simulation for dated measures.

### Creating complex scenarios with simulation modifiers

```{important}
Some policy changes require modifying individual records rather than just changing parameters.
```

Here's how to build a scenario that phases out PIP payments for some claimants over time:

```python
import numpy as np
from policyengine_uk import Scenario, Simulation


def phase_out_pip_gradually(sim: Simulation):
    """Gradually phase out PIP for a proportion of claimants between 2025-2029"""
    # Set random seed for reproducible results
    np.random.seed(42)

    # Create random assignment for each person
    pip_phase_out_seed = np.random.random(len(sim.calculate("person_id")))

    # Define the phase-out period
    start_year = 2025
    end_year = 2029

    # Apply phase-out year by year
    for year in range(start_year, end_year + 1):
        # Get a copy of current PIP payments. calculate returns the
        # simulation's cached array, so write only to a copy and store it
        # with set_input.
        current_pip = np.array(sim.calculate("pip", year))

        # Calculate how far through the phase-out we are
        phase_progress = (year - start_year) / (end_year - start_year)

        # 25% of claimants lose PIP, gradually over the period
        # In year 1, nobody loses it; by final year, 25% have lost it completely
        affected_threshold = 0.25 * phase_progress

        # Set PIP to zero for affected claimants
        current_pip[pip_phase_out_seed < affected_threshold] = 0

        # Apply the modified values back to the simulation
        sim.set_input("pip", year, current_pip)

    return sim


# Create the scenario
pip_phase_out = Scenario(simulation_modifier=phase_out_pip_gradually)

# Test on someone who receives PIP
pip_recipient = {
    "people": {
        "person": {
            "age": {2025: 45},
            "pip": {2025: 150},  # Weekly PIP payment
            "employment_income": {2025: 8_000},
        }
    },
    "benunits": {"benunit": {"members": ["person"]}},
    "households": {"household": {"members": ["person"]}},
}

# Compare baseline and phase-out scenarios
baseline_sim = Simulation(situation=pip_recipient)
reformed_sim = Simulation(situation=pip_recipient, scenario=pip_phase_out)

# Show how PIP changes over the phase-out period
for year in [2025, 2027, 2029]:
    baseline_pip = baseline_sim.calculate("pip", year).mean()
    reformed_pip = reformed_sim.calculate("pip", year).mean()
    print(
        f"{year}: Baseline £{baseline_pip:.0f}/week, with phase-out £{reformed_pip:.0f}/week"
    )
```

### Building Universal Credit scenarios with dynamic changes

Some scenarios need to make changes that depend on the simulation's own data. Here's how to create a UC scenario that adjusts health-element payments based on claimant characteristics:

```python
from policyengine_uk import Scenario, Microsimulation
import numpy as np


def modify_uc_for_new_claimants(sim: Microsimulation):
    """Reduce health elements for new UC claimants while preserving claimant protections"""
    # Access the parameter system to check if reforms are active
    rebalancing_params = (
        sim.tax_benefit_system.parameters.gov.dwp.universal_credit.rebalancing
    )

    # Create random assignment to simulate new vs existing claimants
    np.random.seed(42)
    uc_seed = np.random.random(len(sim.calculate("benunit_id")))

    # Proportion of claimants who are "new" each year (based on real data)
    new_claimant_rates = {
        2025: 0.00,  # No change in 2025
        2026: 0.11,  # 11% are new claimants
        2027: 0.13,
        2028: 0.16,
        2029: 0.22,
    }

    # Apply changes year by year
    for year in range(2026, 2030):
        if not rebalancing_params.active(year):
            continue  # Skip if reforms aren't active this year

        # Identify new claimants
        is_new_claimant = uc_seed < new_claimant_rates[year]

        # Modify a copy of the health element for new claimants (calculate
        # returns the cached array; set_input stores the new values)
        current_health_element = np.array(sim.calculate("uc_LCWRA_element", year))
        new_health_amount = rebalancing_params.new_claimant_health_element(year) * 12

        # Set new amount for new claimants who get health element
        current_health_element[(current_health_element > 0) & is_new_claimant] = (
            new_health_amount
        )

        sim.set_input("uc_LCWRA_element", year, current_health_element)

        # General standard allowance uplifts are already handled in the
        # uc_standard_allowance formula. Scenario modifiers only need to add
        # claimant-specific overrides such as protected health elements.


# Create the UC rebalancing scenario
uc_rebalancing = Scenario(simulation_modifier=modify_uc_for_new_claimants)

# This scenario needs the rebalancing parameters to be active
uc_rebalancing_active = (
    Scenario(parameter_changes={"gov.dwp.universal_credit.rebalancing.active": True})
    + uc_rebalancing
)

# Test on a typical UC claimant
uc_claimant = {
    "people": {
        "person": {
            "age": {2026: 35},
            "employment_income": {2026: 8_000},
            "uc_LCWRA_element": {2026: 390},  # Monthly health element
        }
    },
    "benunits": {"benunit": {"members": ["person"]}},
    "households": {"home": {"members": ["person"], "housing_costs": {2026: 7200}}},
}

baseline_sim = Simulation(situation=uc_claimant)
reformed_sim = Simulation(situation=uc_claimant, scenario=uc_rebalancing_active)

# Compare UC components
for year in [2026, 2028]:
    baseline_uc = baseline_sim.calculate("universal_credit", year).mean()
    reformed_uc = reformed_sim.calculate("universal_credit", year).mean()
    print(
        f"{year}: Baseline UC £{baseline_uc:.0f}/month, reformed £{reformed_uc:.0f}/month"
    )
```

## Analysing scenarios at population level

Use microsimulation to understand the broader impact of your scenarios:

```python
from policyengine_uk import Microsimulation

# Create a major scenario package combining tax cuts and benefit increases
# This represents a significant fiscal intervention
major_scenario = Scenario(
    parameter_changes={
        "gov.hmrc.income_tax.rates.uk[0].rate": 0.15,  # Cut basic rate from 20% to 15%
        "gov.hmrc.income_tax.personal_allowance": 16_000,  # Raise allowance significantly
        "gov.dwp.universal_credit.standard_allowance.single.OVER_25": 600,  # Increase UC by £100/month
        "gov.dwp.universal_credit.means_test.reduction_rate": 0.45,  # Reduce taper from 55% to 45%
    }
)

# Compare baseline and reform
baseline = Microsimulation(
    dataset="hf://policyengine/policyengine-uk-data/enhanced_frs_2022_23.h5"
)
reformed = Microsimulation(
    dataset="hf://policyengine/policyengine-uk-data/enhanced_frs_2022_23.h5",
    scenario=major_scenario,
)

# Calculate the fiscal impact of this major intervention
# Tax cuts reduce revenue, benefit increases raise spending
baseline_revenue = baseline.calculate("income_tax", 2025).sum() / 1e9
reformed_revenue = reformed.calculate("income_tax", 2025).sum() / 1e9
tax_cost = baseline_revenue - reformed_revenue

baseline_uc = baseline.calculate("universal_credit", 2025).sum() / 1e9
reformed_uc = reformed.calculate("universal_credit", 2025).sum() / 1e9
uc_cost = reformed_uc - baseline_uc

total_cost = tax_cost + uc_cost

print(f"Income tax revenue loss: £{tax_cost:.1f}bn")
print(f"UC spending increase: £{uc_cost:.1f}bn")
print(f"Total fiscal cost: £{total_cost:.1f}bn")

# Calculate distributional impact
baseline_poverty = baseline.calculate("in_poverty", 2025).mean()
reformed_poverty = reformed.calculate("in_poverty", 2025).mean()
poverty_reduction = baseline_poverty - reformed_poverty

print(f"Poverty rate reduction: {poverty_reduction:.1%}")
```

## Testing scenarios step by step

When building complex scenarios, test each component separately:

```python
# Build up a complex scenario incrementally to understand each component's impact
# Starting with an empty scenario as our baseline
base_scenario = Scenario(parameter_changes={})

# Add income tax changes
with_tax_changes = base_scenario + Scenario(
    parameter_changes={
        "gov.hmrc.income_tax.rates.uk[0].rate": 0.18,
        "gov.hmrc.income_tax.personal_allowance": 14_000,
    }
)

# Add UC changes
with_uc_changes = with_tax_changes + Scenario(
    parameter_changes={
        "gov.dwp.universal_credit.standard_allowance.single.OVER_25": 500,
        "gov.dwp.universal_credit.means_test.reduction_rate": 0.50,
    }
)

# Add child benefit changes
full_scenario = with_uc_changes + Scenario(
    parameter_changes={
        "gov.hmrc.child_benefit.rates.first_child": 25,
        "gov.hmrc.child_benefit.rates.additional_child": 18,
    }
)

# Test the impact of each addition
test_situation = {
    "people": {
        "parent": {"age": {2025: 30}, "employment_income": {2025: 25_000}},
        "child": {"age": {2025: 6}},
    },
    "benunits": {"family": {"members": ["parent", "child"]}},
    "households": {
        "home": {"members": ["parent", "child"], "housing_costs": {2025: 8400}}
    },  # Annual housing costs
}

# Test each incremental addition to see cumulative effects
scenarios = [
    ("Baseline", base_scenario),
    ("With tax changes", with_tax_changes),
    ("With UC changes", with_uc_changes),
    ("Full package", full_scenario),
]

for name, scenario in scenarios:
    sim = Simulation(situation=test_situation, scenario=scenario)
    net_income = sim.calculate("household_net_income", 2025).mean()
    print(f"{name}: £{net_income / 12:.2f} per month")
```

## Practical tips for scenario design

```{tip}
- Start simple and build complexity gradually
- Test scenarios on multiple household types to understand different impacts
- Use meaningful parameter names and document your choices
- Combine related changes logically (tax reforms with tax reforms, benefit changes with benefit changes)
- Always check the fiscal impact of major reforms
- Consider unintended interactions between different policy areas
```

These techniques let you model complex policy changes that go beyond simple parameter adjustments. Simulation modifiers give you complete control over how the tax-benefit system works, allowing you to implement everything from gradual phase-outs to dynamic eligibility changes. The key is to understand the underlying data structures and use them thoughtfully to represent real policy proposals.
