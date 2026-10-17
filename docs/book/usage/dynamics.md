# Labour supply dynamics

The dynamics module enables modelling of behavioural responses to tax and benefit policy changes. When you change income tax rates or benefit amounts, people may respond by adjusting their work patterns - either changing hours worked (intensive margin) or deciding whether to work at all (extensive margin). This guide shows how to incorporate these dynamic effects into your analysis.

## Understanding labour supply responses

PolicyEngine UK implements the Office for Budget Responsibility's labour supply elasticity framework. The model captures two key behavioural responses:

**Intensive margin (progression)** - How people adjust their working hours in response to changes in take-home pay. Someone facing a higher marginal tax rate might reduce their hours, while someone benefiting from a tax cut might work more.

**Extensive margin (participation)** - Whether people choose to work at all. Changes in the financial reward from working affect decisions to enter or leave employment.

Both responses depend on elasticities that vary by demographic group. The
current `apply_dynamics` coordinator runs progression only: it leaves
participation disabled and returns `participation=None`. The separate
participation function remains available for controlled development work; the
coordinator does not combine its response with progression.

## Basic dynamics calculation

To apply dynamics to any microsimulation, create baseline and reformed simulations, then call `apply_dynamics`:

```python
from policyengine_uk import Microsimulation
from policyengine_uk.model_api import Scenario

# Define baseline and reform scenarios
baseline_scenario = Scenario(
    parameter_changes={
        "gov.hmrc.national_insurance.class_1.rates.employee.main": 0.12,
    }
)

reform_scenario = Scenario(
    parameter_changes={
        "gov.hmrc.national_insurance.class_1.rates.employee.main": 0.10,
    }
)

# Create microsimulations
baseline = Microsimulation(scenario=baseline_scenario)
reformed = Microsimulation(scenario=reform_scenario)

# Set up baseline link and apply dynamics
reformed.baseline.apply_parameter_changes(baseline_scenario.parameter_changes)
dynamics = reformed.apply_dynamics(2025)

# View FTE impacts
print(
    f"Substitution effect FTEs: {dynamics.fte_impacts.substitution_response_ftes:,.0f}"
)
print(f"Income effect FTEs: {dynamics.fte_impacts.income_response_ftes:,.0f}")
if dynamics.fte_impacts.participation_response_ftes is not None:
    print(
        f"Participation FTEs: {dynamics.fte_impacts.participation_response_ftes:,.0f}"
    )
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
if participation is not None:
    print(f"Employment change: {participation['participation_change'].sum():,.0f}")

# FTE impacts provide summary statistics
fte = dynamics.fte_impacts
print(f"Total labour supply response: {fte.ftes:,.0f} FTEs")
```

The progression DataFrame contains individual-level responses including wage
changes, elasticities applied and resulting employment income adjustments.
Participation results are absent from the current coordinator.

### Separate participation calls

`policyengine_uk.dynamics.participation.apply_participation_responses` accepts
an explicit calculation year. Its demographics, adult positions, gain-to-work
counterfactuals and earnings/hours writeback use that year. Direct callers of
`calculate_participation_elasticities` may omit its optional year to retain
the simulation's default-period behaviour. These paths expect the weighted
`Microsimulation` calculation interface; a supplied situation can exercise
them without a population dataset.

Spillovers retain 20 equal-width bins, now bounded by eligible response
candidates only. Adding excluded people cannot move those bounds. The bins,
unweighted within-bin averages, spillover factor and replacement-rate
transformation are inherited model approximations, not methods specified by the
OBR note. The existing exclusions, coefficients, age-18 grouping, wage imputation
and full-time-equivalent quintile placement are unchanged.

A local `numpy.random.RandomState` preserves the legacy MT19937 stream for a
given seed, without changing NumPy's process-global random state. Draws are
consumed in ascending worker-row order, followed by ascending non-worker-row
order, including candidates with zero probabilities or nonpositive imputed
wages. The two draw loops are vectorized with the same candidate order and
storage precision. This does not make stochastic assignments invariant to row
permutations. New entrants' weekly hours are converted to annual hours using the
framework's `WEEKS_IN_YEAR` constant.

These corrections do not activate participation in the coordinator, validate
calibration or certify whole-population speed. Repeated wage imputation and
income recomputations remain, and broader performance/caching work stays open
in [issue1836](https://github.com/PolicyEngine/policyengine-uk/issues/1836).
The separate cohabiting-group correction in PR2445 also needs to be retained at
eventual integration; this branch does not certify that combined landing.

## Analysing distributional effects

Combine dynamics with standard microsimulation analysis to understand how behavioural responses vary across the population:

```python
# Get individual responses
progression = dynamics.progression

# Add demographic information
progression["decile"] = reformed.calculate(
    "household_income_decile", 2025, map_to="person"
)
progression["age_group"] = pd.cut(
    reformed.calculate("age", 2025),
    bins=[0, 30, 50, 65, 100],
    labels=["Under 30", "30-49", "50-64", "65+"],
)

# Analyse by income decile
by_decile = progression.groupby("decile").agg(
    {
        "total_response_ftes": "sum",
        "substitution_response_ftes": "sum",
        "income_response_ftes": "sum",
    }
)

print("FTE changes by income decile:")
print(by_decile.round(0))
```

## Understanding the elasticity framework

The model uses different elasticities for different groups based on empirical evidence:

```python
# Examine elasticities applied
elasticities = progression[["substitution_elasticity", "income_elasticity"]].describe()
print("Elasticity distribution:")
print(elasticities)

# See which groups have different elasticities
progression["has_children"] = reformed.calculate("is_parent", 2025)
by_parent = progression.groupby("has_children")[
    ["substitution_elasticity", "income_elasticity"]
].mean()
print("\nElasticities by parental status:")
print(by_parent)
```

Substitution elasticities range from 0.094 to 0.439 depending on demographics, while income elasticities range from -0.185 to 0; lone fathers are assigned neither. The model excludes certain groups from responses: self-employed workers, students, those aged 60+, and adults beyond the two oldest in each household. Their employment income is left unchanged.

## Validating against OBR estimates

For policies analysed by the OBR, compare your results with their published estimates:

```python
# Example: National Insurance cut from Autumn Statement 2023
# OBR estimated ~94,000 FTE increase

baseline_scenario = Scenario(
    parameter_changes={
        "gov.hmrc.national_insurance.class_1.rates.employee.main": 0.12,
    }
)

reform_scenario = Scenario(
    parameter_changes={
        "gov.hmrc.national_insurance.class_1.rates.employee.main": 0.10,
    }
)

baseline = Microsimulation(scenario=baseline_scenario)
reformed = Microsimulation(scenario=reform_scenario)
reformed.baseline.apply_parameter_changes(baseline_scenario.parameter_changes)

dynamics = reformed.apply_dynamics(2025)
print(f"Modelled FTE increase: {dynamics.fte_impacts.ftes:,.0f}")
print(f"OBR estimate: 94,000")
print(f"Difference: {(dynamics.fte_impacts.ftes - 94_000):+,.0f}")
```

This example runs the current progression-only coordinator. It is not a
validation of the disabled participation route or a promise of agreement with
the OBR total. Data, grouping, imputation and calibration choices also affect
the comparison.

## Elasticity-based responses

Separately from `apply_dynamics`, a reform can set
`gov.simulation.labour_supply_responses.substitution_elasticity` and
`gov.simulation.labour_supply_responses.income_elasticity`. Each person's
`employment_income_behavioral_response` is then their employment income before
responses times the substitution elasticity times `relative_wage_change`, plus
the income elasticity times `relative_income_change`. Both changes compare the
reform with its baseline (`simulation.baseline`), each measured with every
behavioural response switched off and at the reform's earnings and capital
gains before responses: `relative_wage_change` is the relative change in one minus
the marginal tax rate, and `relative_income_change` the relative change in
household net income. The changes are capped at
`gov.simulation.labour_supply_responses.bounds`. The response is part of
`employment_income`, so it feeds into every result that depends on it.

Two things follow from measuring against `simulation.baseline`:

- **The baseline is current law.** `simulation.baseline` is built without the
  reform, whatever policy a comparison treats as its baseline. When two
  simulations are compared and the elasticities are set on the reform side
  only, the reform's response also answers the comparison's baseline policy.
  For a single earner on £30,000 in 2026, the response to a 22% basic rate is
  about -£187, and to that rate plus a £13,000 personal allowance about -£193.
  Compared with the 22% rate costed without responses, the second reform shows
  the whole -£193, not the -£6 or so the allowance adds. Setting the
  elasticities on both sides of the comparison isolates the reform's own
  response.
- **Only earnings and gains are held.** Both measurements take the reform's
  earnings and capital gains before responses. Any other input the reform's
  scenario changes (a data modifier, say, or removing economic assumptions)
  keeps each simulation's own value, so the difference counts as policy in
  `relative_income_change`.

```python
from policyengine_uk import Simulation

situation = {
    "people": {"person": {"age": {2025: 30}, "employment_income": {2025: 40_000}}},
    "benunits": {"benunit": {"members": ["person"]}},
    "households": {"household": {"members": ["person"]}},
}
reformed = Simulation(
    situation=situation,
    reform={
        "gov.hmrc.income_tax.rates.uk[0].rate": {"2025": 0.30},
        "gov.simulation.labour_supply_responses.substitution_elasticity": {
            "2025": 0.25
        },
        "gov.simulation.labour_supply_responses.income_elasticity": {"2025": -0.05},
    },
)
# The marginal rate rises from 28% to 38%, so the wage after tax falls by 5/36,
# and net income falls by £2,743 of £32,145: a response of about -£1,218.
print(reformed.calculate("employment_income_behavioral_response", 2025))
```

Unlike these labour supply elasticities, which are zero unless a reform sets
them, capital gains respond to reforms by default: see the
[capital gains realisation response](../assumptions/capital-gains-responses.md).

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

The size of these limitations has not been established for every reform.
Participation calibration and broader performance work remain outside these
implementation corrections.