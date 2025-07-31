# Running simulations

The `Simulation` class is the heart of PolicyEngine UK - it calculates tax and benefit outcomes for people and households. This guide walks you through everything from basic calculations to advanced microsimulation analysis.

## Creating your first simulation

Every simulation starts with a situation that describes the people, benefit units, and households you want to analyse:

```python
from policyengine_uk import Simulation

situation = {
    "people": {
        "person_1": {
            "age": {2025: 30},
            "employment_income": {2025: 30_000}
        }
    },
    "benunits": {
        "benunit_1": {
            "members": ["person_1"]
        }
    },
    "households": {
        "household_1": {
            "members": ["person_1"]
        }
    }
}

sim = Simulation(situation=situation)
income_tax = sim.calculate("income_tax", 2025)
print(f"Income tax: £{income_tax[0]:.2f}")
```

This creates a simulation for one person and calculates their annual income tax liability. The result shows they would pay £3,486 per year in income tax.

## Understanding the situation structure

The situation dictionary has three main sections:

**People** define individuals with their characteristics:
```python
"people": {
    "sarah": {
        "age": {2025: 28},
        "employment_income": {2025: 35_000},
        "pension_contributions": {2025: 2_800}
    },
    "tom": {
        "age": {2025: 32},
        "self_employment_income": {2025: 18_000}
    }
}
```

**Benefit units** group people for benefit calculations (typically families):
```python
"benunits": {
    "family": {
        "members": ["sarah", "tom"]
    }
}
```

**Households** group people who live together:
```python
"households": {
    "home": {
        "members": ["sarah", "tom"],
        "housing_costs": {2025: 11400},  # Annual rent
        "council_tax": {2025: 1_800}   # Annual
    }
}
```

## Calculating different variables

PolicyEngine UK can calculate hundreds of variables. Here are some common ones:

```python
# Taxes
income_tax = sim.calculate("income_tax", 2025)
national_insurance = sim.calculate("national_insurance", 2025)
council_tax = sim.calculate("council_tax", 2025)

# Benefits
universal_credit = sim.calculate("universal_credit", 2025)
child_benefit = sim.calculate("child_benefit", 2025)
state_pension = sim.calculate("state_pension", 2025)

# Summary measures
net_income = sim.calculate("household_net_income", 2025)
in_poverty = sim.calculate("in_poverty", 2025)
marginal_tax_rate = sim.calculate("marginal_tax_rate", 2025)
```

These calculations return arrays because simulations can handle multiple people, benefit units or households simultaneously. Each variable gives you results at the appropriate level - income tax is calculated per person, Universal Credit per benefit unit, and council tax per household.

## Simulating policy scenarios

To test policy changes, create a scenario and apply it to your simulation. This example shows what happens when we increase Universal Credit's standard allowance for single people over 25 from the current rate to £500 per month:

```python
from policyengine_uk import Scenario

# Create a scenario that increases UC standard allowance
scenario = Scenario(parameter_changes={
    "gov.dwp.universal_credit.standard_allowance.single.OVER_25": 500
})

# Apply the scenario to create a new simulation
reformed_sim = Simulation(situation=situation, scenario=scenario)

# Compare the average UC payment between baseline and scenario
baseline_uc = sim.calculate("universal_credit", 2025).mean()
reformed_uc = reformed_sim.calculate("universal_credit", 2025).mean()

# Calculate the difference to see the policy impact
difference = reformed_uc - baseline_uc
print(f"Average UC increase: £{difference:.2f} per month")
```

## Working with families and children

Family situations require more detailed setup:

```python
family_with_children = {
    "people": {
        "parent": {
            "age": {2025: 35},
            "employment_income": {2025: 28_000}
        },
        "partner": {
            "age": {2025: 33},
            "employment_income": {2025: 12_000}
        },
        "child_1": {
            "age": {2025: 7}
        },
        "child_2": {
            "age": {2025: 4}
        }
    },
    "benunits": {
        "family": {
            "members": ["parent", "partner", "child_1", "child_2"]
        }
    },
    "households": {
        "home": {
            "members": ["parent", "partner", "child_1", "child_2"],
            "housing_costs": {2025: 9600},  # Annual housing costs
            "childcare_costs": {2025: 7200}  # Annual childcare costs
        }
    }
}

family_sim = Simulation(situation=family_with_children)

# Calculate family-specific benefits - these are per benefit unit (family)
child_benefit = family_sim.calculate("child_benefit", 2025).mean()
childcare_support = family_sim.calculate("universal_credit_childcare", 2025).mean()

print(f"Child benefit: £{child_benefit:.2f} per month")
print(f"Childcare support: £{childcare_support:.2f} per month")
```

## Using different data sources

### From pandas DataFrames

If you have data in a DataFrame, convert it to the right format:

```python
import pandas as pd

# Your data needs specific column naming
df = pd.DataFrame({
    "person_id__2025": [1, 2, 3],
    "age__2025": [25, 45, 65],
    "employment_income__2025": [20000, 40000, 0],
    "state_pension__2025": [0, 0, 180]  # Weekly pension
})

# Create simulation from the DataFrame
sim_from_df = Simulation(dataset=df)
# Calculate total income tax across all people in the dataset
total_tax = sim_from_df.calculate("income_tax", 2025).sum()
print(f"Total income tax from all people: £{total_tax:.2f}")
```

The column naming follows the pattern `variable_name__year` for time-varying variables.

### From survey datasets

For population-level analysis, use survey data:

```python
from policyengine_uk import Microsimulation

# Load the Enhanced Family Resources Survey
sim = Microsimulation(
    dataset="hf://policyengine/policyengine-uk-data/enhanced_frs_2022_23.h5"
)

# Calculate population totals using survey weights
# This gives us an estimate for the entire UK population
total_income_tax = sim.calculate("income_tax", 2025).sum() / 1e9
print(f"Total UK income tax revenue: £{total_income_tax:.1f}bn")
```

## Microsimulation analysis

The `Microsimulation` class extends `Simulation` with survey weights for population estimates:

```python
from policyengine_uk import Microsimulation

# Compare baseline and reform
baseline = Microsimulation(
    dataset="hf://policyengine/policyengine-uk-data/enhanced_frs_2022_23.h5"
)

# Create a scenario that increases the basic rate of income tax to 25%
scenario = Scenario(parameter_changes={
    "gov.hmrc.income_tax.rates.uk[0].rate": 0.25
})
reformed = Microsimulation(
    dataset="hf://policyengine/policyengine-uk-data/enhanced_frs_2022_23.h5",
    scenario=scenario
)

# Calculate revenue impact by comparing household net incomes
# When net income falls, government revenue increases
baseline_net = baseline.calculate("household_net_income", 2025)
reformed_net = reformed.calculate("household_net_income", 2025)

# The negative of the income change gives us the revenue change
revenue_change = -(reformed_net - baseline_net).sum() / 1e9
print(f"Additional government revenue: £{revenue_change:.1f}bn")

# Analyse distributional impact by looking at poverty rates
# in_poverty is a boolean variable, so mean() gives us the poverty rate
poverty_baseline = baseline.calculate("in_poverty", 2025).mean()
poverty_reformed = reformed.calculate("in_poverty", 2025).mean()

poverty_change = poverty_reformed - poverty_baseline
print(f"Poverty rate change: {poverty_change:.1%}")
```

## Advanced techniques

### Understanding caching behavior

```{warning}
Variables and parameters are cached once calculated to improve performance, but this can affect dynamic scenarios.
```

```python
# Variables are cached once you calculate them
income_tax = sim.calculate("income_tax", 2025)  # Cached after first calculation
# Subsequent calls return the cached value unless inputs change

# To insert new values, use set_input with arrays
current_income = sim.calculate("employment_income", 2025)
new_income = current_income * 0 + 35_000  # Create array with new values
sim.set_input("employment_income", 2025, new_income)  # This will invalidate related caches

# Parameters are also cached when requested
parameters = sim.tax_benefit_system.parameters(2025)  # Cached for 2025

# If you have a reform that changes parameters after requesting them:
scenario = Scenario(parameter_changes={
    "gov.hmrc.income_tax.rates.uk[0].rate": 0.25
})
# The parameter change won't take effect unless you reset the cache:
sim.tax_benefit_system.reset_parameter_caches()
```

### Calculating multiple variables efficiently

Instead of calculating variables one by one, you can get multiple results at once using the built-in `calculate_dataframe` method:

```python
# Get multiple variables in a single DataFrame
variables = ["employment_income", "income_tax", "universal_credit", "household_net_income"]
results_df = sim.calculate_dataframe(variables, 2025)

# This gives you a DataFrame with columns for each variable
print(results_df.head())
print(f"Average net income: £{results_df['household_net_income'].mean():.2f}")
```

### Working with different time periods

```python
# Multi-year analysis to see how income changes over time
years = [2023, 2024, 2025]
income_by_year = {}

for year in years:
    income_by_year[year] = sim.calculate("household_net_income", year)

# Compare average household income across years
for year in years:
    avg_income = income_by_year[year].mean()
    print(f"{year}: £{avg_income/12:.2f} per month")
```

### Mapping variables to different entities

Some variables can be calculated at different levels:

```python
# Calculate employment income at different entity levels
# Individual level - one value per person
person_income = sim.calculate("employment_income", 2025)
print(f"Average personal employment income: £{person_income.mean():.2f}")

# Household level - sums all employment income within each household
household_income = sim.calculate("employment_income", 2025, map_to="household")
print(f"Average household employment income: £{household_income.mean():.2f}")

# Benefit unit level - sums employment income within each benefit unit (family)
benunit_income = sim.calculate("employment_income", 2025, map_to="benunit")
print(f"Average benefit unit employment income: £{benunit_income.mean():.2f}")
```

### Using custom weights

For microsimulation with custom weights:

```python
# Access and modify survey weights for sensitivity analysis
weights = sim.get_weights("income_tax", 2025)
modified_weights = weights * 1.1  # Increase all weights by 10%

# Calculate population total with modified weights
unweighted_values = sim.calculate("income_tax", 2025, use_weights=False)
weighted_total = (unweighted_values * modified_weights).sum()
print(f"Total with 10% higher weights: £{weighted_total/1e9:.1f}bn")
```

## Debugging simulations

When simulations don't behave as expected:

```python
# Check individual components to understand the tax calculation
# These help you trace through how income tax is calculated step by step
employment_income = sim.calculate("employment_income", 2025).mean()
personal_allowance = sim.calculate("personal_allowance", 2025).mean()
taxable_income = sim.calculate("adjusted_net_income", 2025).mean()
income_tax = sim.calculate("income_tax", 2025).mean()

print(f"Employment income: £{employment_income:.2f}")
print(f"Personal allowance: £{personal_allowance:.2f}")
print(f"Taxable income: £{taxable_income:.2f}")
print(f"Income tax: £{income_tax:.2f}")

# Verify the household composition was interpreted correctly
avg_age = sim.calculate("age", 2025).mean()
children_per_household = sim.calculate("household_count_children", 2025).mean()
print(f"Average age: {avg_age:.1f} years")
print(f"Average children per household: {children_per_household:.1f}")
```

## Performance tips

- Use `Microsimulation` for population analysis, `Simulation` for household-level work
- Calculate multiple variables in batches rather than individually
- For large datasets, consider calculating subsets first to verify your logic
- Cache simulation results when running the same calculation multiple times

The simulation system is designed to be flexible and powerful. Start with simple examples and gradually build up to more complex analyses as you become familiar with the structure and capabilities.