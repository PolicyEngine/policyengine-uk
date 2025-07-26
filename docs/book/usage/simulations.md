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

### Data sources

Simulations can be created from various data sources:

#### DataFrames

```python
import pandas as pd

df = pd.DataFrame({
    "person_id__2023": [1, 2, 3],
    "age__2023": [25, 30, 35],
    "employment_income__2023": [20000, 30000, 40000],
    # ... other columns
})

sim = Simulation(dataset=df)
```

#### HuggingFace locations

```python
# Load from HuggingFace
sim = Simulation(dataset="hf://policyengine/policyengine-uk-data/enhanced_frs_2023_24.h5")
```

#### From PolicyEngine-Core Dataset objects

```python
from policyengine_uk.data import EnhancedFRS

# Using the Enhanced FRS dataset
dataset = EnhancedFRS()
sim = Simulation(dataset=dataset)
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
from policyengine_uk import Microsimulation

# Create from weighted dataset
sim = Microsimulation(dataset="hf://policyengine/policyengine-uk-data/enhanced_frs_2023_24.h5")

# Calculate with weights
poverty_rate = sim.calculate("in_poverty", "2023").mean()
print(f"Poverty rate: {poverty_rate:.1%}")

# Get total government revenue
income_tax_revenue = sim.calculate("income_tax", "2023").sum()
print(f"Total income tax: £{income_tax_revenue/1e9:.1f}bn")
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
