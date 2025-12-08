# Labour supply dynamics

The dynamics module enables modelling of behavioural responses to tax and benefit policy changes. When you change income tax rates or benefit amounts, people may respond by adjusting their work patterns - either changing hours worked (intensive margin) or deciding whether to work at all (extensive margin). This guide shows how to incorporate these dynamic effects into your analysis.

## Understanding labour supply responses

PolicyEngine UK implements the Office for Budget Responsibility's labour supply elasticity framework. The model captures two key behavioural responses:

**Intensive margin (progression)** - How people adjust their working hours in response to changes in take-home pay. Someone facing a higher marginal tax rate might reduce their hours, while someone benefiting from a tax cut might work more.

**Extensive margin (participation)** - Whether people choose to work at all. Changes in the financial reward from working affect decisions to enter or leave employment.

Both responses depend on elasticities that vary by demographic group, following empirical evidence on how different populations respond to policy changes.

## Basic dynamics calculation

To apply dynamics to any microsimulation, create baseline and reformed simulations, then call `apply_dynamics`:

```python
from policyengine_uk import Microsimulation
from policyengine_uk.model_api import Scenario

# Define baseline and reform scenarios
baseline_scenario = Scenario(parameter_changes={
    "gov.hmrc.national_insurance.class_1.rates.employee.main": 0.12,
})

reform_scenario = Scenario(parameter_changes={
    "gov.hmrc.national_insurance.class_1.rates.employee.main": 0.10,
})

# Create microsimulations
baseline = Microsimulation(scenario=baseline_scenario)
reformed = Microsimulation(scenario=reform_scenario)

# Set up baseline link and apply dynamics
reformed.baseline.apply_parameter_changes(baseline_scenario.parameter_changes)
dynamics = reformed.apply_dynamics(2025)

# View FTE impacts
print(f"Substitution effect FTEs: {dynamics.fte_impacts.substitution_response_ftes:,.0f}")
print(f"Income effect FTEs: {dynamics.fte_impacts.income_response_ftes:,.0f}")
print(f"Participation FTEs: {dynamics.fte_impacts.participation_response_ftes:,.0f}")
print(f"Total FTE change: {dynamics.fte_impacts.ftes:,.0f}")
```

This example models a 2 percentage point cut in National Insurance contributions and calculates the resulting change in full-time equivalent employment.

## Working with dynamics results

The `apply_dynamics` method returns a `LabourSupplyResponseData` object containing detailed results:

```python
# Access progression responses (intensive margin)
progression = dynamics.progression
print(f"Workers affected: {len(progression):,}")
print(f"Average hours change: {progression['total_response_ftes'].mean():.3f} FTEs")

# Access participation responses (extensive margin)
participation = dynamics.participation
print(f"Employment change: {participation['participation_change'].sum():,.0f}")

# FTE impacts provide summary statistics
fte = dynamics.fte_impacts
print(f"Total labour supply response: {fte.ftes:,.0f} FTEs")
```

The progression DataFrame contains individual-level responses including wage changes, elasticities applied, and resulting employment income adjustments. The participation DataFrame shows employment status changes and associated FTE impacts.

## Analysing distributional effects

Combine dynamics with standard microsimulation analysis to understand how behavioural responses vary across the population:

```python
# Get individual responses
progression = dynamics.progression

# Add demographic information
progression['decile'] = reformed.calculate("household_income_decile", 2025, map_to="person")
progression['age_group'] = pd.cut(
    reformed.calculate("age", 2025), 
    bins=[0, 30, 50, 65, 100],
    labels=["Under 30", "30-49", "50-64", "65+"]
)

# Analyse by income decile
by_decile = progression.groupby('decile').agg({
    'total_response_ftes': 'sum',
    'substitution_response_ftes': 'sum',
    'income_response_ftes': 'sum'
})

print("FTE changes by income decile:")
print(by_decile.round(0))
```

## Understanding the elasticity framework

The model uses different elasticities for different groups based on empirical evidence:

```python
# Examine elasticities applied
elasticities = progression[['substitution_elasticity', 'income_elasticity']].describe()
print("Elasticity distribution:")
print(elasticities)

# See which groups have different elasticities
progression['has_children'] = reformed.calculate("is_parent", 2025)
by_parent = progression.groupby('has_children')[
    ['substitution_elasticity', 'income_elasticity']
].mean()
print("\nElasticities by parental status:")
print(by_parent)
```

Substitution elasticities range from 0.14 to 0.30 depending on demographics, while income elasticities range from -0.185 to 0. The model excludes certain groups from responses: self-employed workers, students, those aged 60+, and secondary earners beyond the first adult.

## Validating against OBR estimates

For policies analysed by the OBR, compare your results with their published estimates:

```python
# Example: National Insurance cut from Autumn Statement 2023
# OBR estimated ~94,000 FTE increase

baseline_scenario = Scenario(parameter_changes={
    "gov.hmrc.national_insurance.class_1.rates.employee.main": 0.12,
})

reform_scenario = Scenario(parameter_changes={
    "gov.hmrc.national_insurance.class_1.rates.employee.main": 0.10,
})

baseline = Microsimulation(scenario=baseline_scenario)
reformed = Microsimulation(scenario=reform_scenario)
reformed.baseline.apply_parameter_changes(baseline_scenario.parameter_changes)

dynamics = reformed.apply_dynamics(2025)
print(f"Modelled FTE increase: {dynamics.fte_impacts.ftes:,.0f}")
print(f"OBR estimate: 94,000")
print(f"Difference: {(dynamics.fte_impacts.ftes - 94_000):+,.0f}")
```

Small differences from OBR estimates can arise from data vintage, population projections, or minor methodological variations.

## Technical implementation details

The dynamics calculation proceeds through several steps:

1. **Marginal rate calculation** - Computes effective marginal tax rates by simulating small income changes
2. **Elasticity application** - Applies group-specific elasticities to wage and income changes  
3. **Response calculation** - Determines employment income adjustments based on elasticities
4. **FTE conversion** - Translates income changes to full-time equivalent employment

The model follows OBR methodology when the `gov.dynamic.obr_labour_supply_assumptions` parameter is true (default for 2024 onwards).

## Limitations and considerations

When using dynamics, be aware of these limitations:

- The model assumes no general equilibrium effects (wages don't adjust)
- Elasticities are based on historical evidence and may not apply to very large reforms
- Self-employed workers are excluded as their labour supply is harder to model
- The model doesn't capture long-term effects like human capital accumulation

For most tax and benefit reforms, these limitations don't significantly affect the results. The framework provides robust estimates aligned with fiscal policy analysis standards.