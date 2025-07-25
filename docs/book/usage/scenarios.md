# PolicyEngine UK API documentation

## Overview

PolicyEngine UK provides a simulation framework for modeling tax and benefit systems. The two core classes, `Scenario` and `Simulation`, work together to enable policy analysis and microsimulation.

## Scenario

The `Scenario` class represents a configuration for policy simulations, allowing you to define parameter changes and custom modifications to apply to simulations.

### Basic usage

```python
from policyengine_uk import Scenario, Simulation

# Create a scenario with parameter changes
scenario = Scenario(
    parameter_changes={
        "gov.hmrc.income_tax.rates.uk[0].rate": 0.15,  # Change basic rate to 15%
        "gov.dwp.universal_credit.standard_allowance.single.OVER_25": 400
    }
)

# Apply to a simulation
sim = Simulation(scenario=scenario)
```

### Creating scenarios from reforms

```python
from policyengine_uk import Scenario
from policyengine_uk.reforms import BasicIncomeReform

# From a Reform class
scenario = Scenario.from_reform(BasicIncomeReform)

# From a dictionary of parameter changes
scenario = Scenario.from_reform({
    "gov.hmrc.income_tax.rates.uk[0].rate": 0.25
})
```

### Combining scenarios

Scenarios can be combined using the `+` operator:

```python
# Create two scenarios
tax_scenario = Scenario(
    parameter_changes={"gov.hmrc.income_tax.rates.uk[0].rate": 0.15}
)

benefit_scenario = Scenario(
    parameter_changes={"gov.dwp.universal_credit.standard_allowance.single.OVER_25": 400}
)

# Combine them
combined_scenario = tax_scenario + benefit_scenario
```

### Custom simulation modifiers

For modifications beyond parameter changes:

```python
def add_new_benefit(simulation):
    # Custom logic to add a new benefit to the simulation
    simulation.add_variable(MyNewBenefit)

scenario = Scenario(
    simulation_modifier=add_new_benefit
)
```

### API reference

#### Constructor

```python
Scenario(
    parameter_changes: Optional[Dict[str, Union[int, float, bool, Dict]]] = None,
    simulation_modifier: Optional[Callable[[Simulation], None]] = None
)
```

**Parameters:**
- `parameter_changes`: Dictionary mapping parameter paths to new values
- `simulation_modifier`: Function that takes a Simulation and modifies it

#### Methods

##### `from_reform(reform: Union[tuple, dict, Type[Reform]]) -> Scenario`
Create a Scenario from various reform representations.

##### `apply(simulation: Simulation) -> None`
Apply the scenario to a simulation instance.

##### `__add__(other: Scenario) -> Scenario`
Combine two scenarios. Parameter changes are merged (with the second scenario taking precedence in conflicts), and simulation modifiers are chained.
