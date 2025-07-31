# Getting started

PolicyEngine UK helps you analyse the UK tax and benefit system in two main ways: simulating policies for specific households, or running large-scale microsimulation analyses. The first requires just a few minutes of setup, while the second needs access to survey data and takes a bit longer to configure.

```{tip}
If possible, use Google Colab - it's free and ensures everyone uses the same computing environment.
```

The full microsimulation model needs just this snippet:

```python
!export HUGGING_FACE_TOKEN=<your_token>
!pip install policyengine-uk
```

## Installing PolicyEngine UK

Install the package like any other Python library (requires Python ≥3.7):

```bash
pip install policyengine-uk
```

## Your first household simulation

Let's start with a simple example: calculating how much income tax a 30-year-old earning £30,000 would pay.

```python
from policyengine_uk import Simulation

# Define the household situation
situation = {
    "people": {
        "person": {
            "age": {2025: 30},
            "employment_income": {2025: 30_000},
        },
    },
    "benunits": {
        "benunit": {
            "members": ["person"],
        },
    },
    "households": {
        "household": {
            "members": ["person"],
        }
    },
}

# Create and run the simulation
simulation = Simulation(situation=situation)
income_tax = simulation.calculate("income_tax", 2025)
print(f"Income tax: £{income_tax[0]:.2f}")
```

This gives us £3,486 in income tax.

```{note}
The structure might look complex at first, but it reflects how the UK tax system works - people belong to benefit units (families for benefit purposes) and households (for housing costs and council tax).
```

## Analysing a policy reform

Now let's see what happens if we increase the basic rate of income tax from 20% to 25%:

```python
# Define the policy reform
increase_basic_rate = {"gov.hmrc.income_tax.rates.uk[0].rate": 0.25}

# Compare baseline and reformed systems
baseline = Simulation(situation=situation)
reformed = Simulation(situation=situation, reform=increase_basic_rate)

baseline_tax = baseline.calculate("income_tax", 2025)[0]
reformed_tax = reformed.calculate("income_tax", 2025)[0]

increase = reformed_tax - baseline_tax
print(f"Tax increase: £{increase:.2f}")
```

The reform increases this person's tax by £871.50 per year.

```{important}
Policy parameters use a hierarchical structure - here we're changing the first UK income tax rate (`uk[0].rate`), which is the basic rate.
```

## Running microsimulation analyses

```{warning}
To analyse policies across the entire population, you'll need survey data. PolicyEngine provides processed datasets via HuggingFace, but you'll need an account and access token.
```

1. Create a [HuggingFace account](https://huggingface.co)
2. Generate a personal access token in your settings
3. Set it as an environment variable:

```bash
export HUGGING_FACE_TOKEN=your_token_here
```

### Your first population analysis

Here's how to calculate total Universal Credit spending across the UK:

```python
from policyengine_uk import Microsimulation

# Load the enhanced Family Resources Survey data
sim = Microsimulation(
    dataset="hf://policyengine/policyengine-uk-data/enhanced_frs_2022_23.h5"
)

# Calculate total UC spending (in billions)
total_uc = sim.calculate("universal_credit", 2025).sum() / 1e9
print(f"Total Universal Credit spending: £{total_uc:.1f}bn")
```

This shows approximately £79.4bn in Universal Credit spending.

### Estimating revenue from reforms

Let's apply the same basic rate increase to the entire population:

```python
# Set up baseline and reformed simulations
DATASET = "hf://policyengine/policyengine-uk-data/enhanced_frs_2022_23.h5"

baseline = Microsimulation(dataset=DATASET)
reformed = Microsimulation(dataset=DATASET, reform=increase_basic_rate)

# Calculate the revenue impact
baseline_income = baseline.calculate("household_net_income", 2025)
reformed_income = reformed.calculate("household_net_income", 2025)

revenue = -(reformed_income - baseline_income).sum() / 1e9
print(f"Additional revenue: £{revenue:.1f}bn per year")
```

```{note}
Revenue is calculated as the negative of household net income changes - when households have less net income, government revenue increases.
```

The reform would raise approximately £35.5bn annually.

## Working with complex households

Real households often have multiple people, children, and various income sources. Here's a family with two adults and two children:

```python
family_situation = {
    "people": {
        "parent_1": {
            "age": {2025: 35},
            "employment_income": {2025: 25_000},
        },
        "parent_2": {
            "age": {2025: 33},
            "employment_income": {2025: 15_000},
        },
        "child_1": {
            "age": {2025: 8},
        },
        "child_2": {
            "age": {2025: 5},
        },
    },
    "benunits": {
        "family": {
            "members": ["parent_1", "parent_2", "child_1", "child_2"],
        },
    },
    "households": {
        "home": {
            "members": ["parent_1", "parent_2", "child_1", "child_2"],
            "housing_costs": {2025: 9600},  # Annual rent
        }
    },
}

family_sim = Simulation(situation=family_situation)

# Calculate various benefits and taxes
child_benefit = family_sim.calculate("child_benefit", 2025)[0]
universal_credit = family_sim.calculate("universal_credit", 2025)[0]
total_tax = family_sim.calculate("income_tax", 2025).sum()

print(f"Child benefit: £{child_benefit:.2f}")
print(f"Universal Credit: £{universal_credit:.2f}")
print(f"Total income tax: £{total_tax:.2f}")
```

## Next steps

You're now ready to explore PolicyEngine UK further.

```{tip}
The [PolicyEngine web app](https://policyengine.org) includes a 'Reproduce in Python' section at the bottom of each page, which generates code snippets for any household or reform you create there.
```

For more detailed guidance, see:
- [Simulations](simulations.md) - comprehensive guide to running simulations
- [Scenarios](scenarios.md) - creating and combining policy reforms