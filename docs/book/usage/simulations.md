## Simulation

The `Simulation` class calculates tax and benefit outcomes for individuals and households in the UK tax-benefit system.

### Basic usage

```python
from policyengine_uk import Simulation

# Create from a situation dictionary
sim = Simulation(situation={
    "people": {
        "person_1": {
            "age": {"2023": 30},
            "employment_income": {"2023": 30000}
        }
    },
    "households": {
        "household_1": {
            "members": ["person_1"]
        }
    }
})

# Calculate a variable
income_tax = sim.calculate("income_tax", "2023")
```

### Using scenarios

Apply policy changes using the `Scenario` class:

```python
from policyengine_uk import Simulation, Scenario

# Create a scenario with policy changes
scenario = Scenario(parameter_changes={
    "gov.hmrc.income_tax.rates.uk[0].rate": 0.15,  # Reduce basic rate to 15%
    "gov.dwp.universal_credit.standard_allowance.single.OVER_25": 400
})

# Apply scenario to simulation
sim = Simulation(
    scenario=scenario,
    situation={
        "people": {
            "person_1": {
                "age": {"2023": 30},
                "employment_income": {"2023": 25000}
            }
        },
        "households": {
            "household_1": {
                "members": ["person_1"]
            }
        }
    }
)

# Calculate variables under the reformed system
income_tax = sim.calculate("income_tax", "2023")
universal_credit = sim.calculate("universal_credit", "2023")
```

### Data sources

Simulations can be created from various data sources:

#### DataFrames

```python
import pandas as pd
from policyengine_uk import Simulation, Scenario

df = pd.DataFrame({
    "person_id__2023": [1, 2, 3],
    "age__2023": [25, 30, 35],
    "employment_income__2023": [20000, 30000, 40000],
    # ... other columns
})

# With policy reforms
scenario = Scenario(parameter_changes={
    "gov.hmrc.income_tax.rates.uk[0].rate": 0.18
})

sim = Simulation(dataset=df, scenario=scenario)
```

#### HuggingFace locations

```python
from policyengine_uk import Simulation, Scenario

# Apply reforms to representative data
scenario = Scenario(parameter_changes={
    "gov.dwp.universal_credit.rebalancing.active": True
})

sim = Simulation(
    dataset="hf://policyengine/policyengine-uk-data/enhanced_frs_2023_24.h5",
    scenario=scenario
)
```

#### From PolicyEngine-Core Dataset objects

```python
from policyengine_uk.data import EnhancedFRS
from policyengine_uk import Simulation, Scenario

# Using the Enhanced FRS dataset with reforms
dataset = EnhancedFRS()
scenario = Scenario(parameter_changes={
    "gov.hmrc.income_tax.personal_allowance": 15000  # Increase personal allowance
})

sim = Simulation(dataset=dataset, scenario=scenario)
```

### Calculating variables

```python
# Calculate for all entities
income_tax = sim.calculate("income_tax", "2023")

# Calculate with mapping to different entity
household_income = sim.calculate("employment_income", "2023", map_to="household")
```

### Microsimulation

The `Microsimulation` class extends `Simulation` with survey weights for population-level analysis.

```python
from policyengine_uk import Microsimulation, Scenario

# Create scenario for analysis
scenario = Scenario(parameter_changes={
    "gov.dwp.universal_credit.standard_allowance.single.OVER_25": 500  # £500/month
})

# Create microsimulation with weights and reforms
sim = Microsimulation(
    dataset="hf://policyengine/policyengine-uk-data/enhanced_frs_2023_24.h5",
    scenario=scenario
)

# Calculate impact with weights
poverty_rate = sim.calculate("in_poverty", "2023").mean()
print(f"Poverty rate under reform: {poverty_rate:.1%}")

# Get total government revenue impact
income_tax_revenue = sim.calculate("income_tax", "2023").sum()
print(f"Total income tax revenue: £{income_tax_revenue/1e9:.1f}bn")
```

### Comparing baseline and reform scenarios

```python
from policyengine_uk import Microsimulation, Scenario

# Baseline simulation
baseline_sim = Microsimulation(
    dataset="hf://policyengine/policyengine-uk-data/enhanced_frs_2023_24.h5"
)

# Reform scenario
reform_scenario = Scenario(parameter_changes={
    "gov.hmrc.income_tax.rates.uk[0].rate": 0.25  # Increase basic rate to 25%
})

reform_sim = Microsimulation(
    dataset="hf://policyengine/policyengine-uk-data/enhanced_frs_2023_24.h5",
    scenario=reform_scenario
)

# Compare outcomes
baseline_revenue = baseline_sim.calculate("income_tax", "2023").sum()
reform_revenue = reform_sim.calculate("income_tax", "2023").sum()

revenue_change = reform_revenue - baseline_revenue
print(f"Additional revenue: £{revenue_change/1e9:.1f}bn")
```

### Working with weights

```python
# Calculate without weights for debugging
values = sim.calculate("income_tax", "2023", use_weights=False)

# Access weights directly
weights = sim.get_weights("income_tax", "2023")

# Calculate multiple variables as weighted DataFrame
df = sim.calculate_dataframe(
    ["employment_income", "income_tax", "universal_credit"],
    "2023"
)
```