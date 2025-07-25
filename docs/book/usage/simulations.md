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

#### From a DataFrame

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

#### From a HuggingFace dataset

```python
# Load from HuggingFace
sim = Simulation(dataset="hf://policyengine/policyengine-uk-data/enhanced_frs_2023_24.h5")
```

#### From UK dataset objects

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

### Working with branches

Simulations support branching for comparing different scenarios:

```python
# Create baseline simulation
baseline = Simulation(dataset=my_data)

# Create reform branch
reform = baseline.clone()
reform.set_input("universal_credit", "2023", [500])

# Compare results
baseline_poverty = baseline.calculate("in_poverty", "2023")
reform_poverty = reform.calculate("in_poverty", "2023")
```

### API reference

#### Constructor

```python
Simulation(
    scenario: Optional[Scenario] = None,
    situation: Optional[Dict] = None,
    dataset: Optional[Union[pd.DataFrame, str, Dataset]] = None,
    trace: bool = False
)
```

**Parameters:**
- `scenario`: A Scenario object defining parameter changes and modifications
- `situation`: Dictionary describing household composition and characteristics
- `dataset`: Data source (DataFrame, URL, or Dataset object)
- `trace`: Enable detailed calculation tracing for debugging

#### Key methods

##### `calculate(variable_name: str, period: str = None, map_to: str = None) -> np.ndarray`
Calculate values for a variable.

**Parameters:**
- `variable_name`: Name of the variable to calculate
- `period`: Time period (e.g., "2023", "2023-01")
- `map_to`: Entity to map results to (e.g., "household")

##### `set_input(variable_name: str, period: str, value: Union[np.ndarray, float])`
Set input values for a variable.

##### `get_holder(variable_name: str) -> Holder`
Get the holder object for a variable (advanced usage).

---

## Microsimulation

The `Microsimulation` class extends `Simulation` with survey weights for population-level analysis.

### Basic usage

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
