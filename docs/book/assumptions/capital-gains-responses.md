# Capital gains realisation response

People choose when to realise capital gains, so a change in the tax on gains
changes the gains realised. PolicyEngine UK models this realisation response
for every reform: by default, realised gains respond at a retention-rate
elasticity of 1.

## How the response works

A reform scales each person's realised gains by

$$
G_1 = G_0 \times \left(\frac{1 - t_1}{1 - t_0}\right)^{e}
$$

where $G_0$ is their gains before the response (`capital_gains_before_response`),
$t_0$ and $t_1$ their marginal rates on gains under the baseline's and the
reform's rules, and $e$ the elasticity. $1 - t$ is the retention rate, the
share of a marginal pound of gains kept after tax.

- **The rates.** Each rate is `marginal_tax_rate_on_capital_gains`, a
  share-weighted marginal rate across the person's schedules (main rates,
  Business Asset Disposal Relief, residential property, carried interest).
  Both are measured at the person's gains before the response, with every
  behavioural response switched off, so their difference reflects the reform
  alone.
- **The schedules.** Gains qualifying for Business Asset Disposal Relief or
  Investors' Relief respond at `capital_gains_badr_elasticity`, and the rest at
  `capital_gains_elasticity`, both to the same change in the person's rate.
- **The result.** `capital_gains` is the gains before the response plus
  `capital_gains_behavioural_response`, and `capital_gains_tax` charges the
  realised gains.

## The default assumption

`gov.simulation.capital_gains_responses.elasticity` is 1.0, and gains
qualifying for the relief take the same 1.0. This is PolicyEngine's central
assumption: the value Advani, Lonsdale and Summers (2024, pp. 36–37) use for
the medium term, with the range they consider, 0.5 to 2.0, as sensitivities.

The assumption has limits:

- **It isn't an estimate for every reform.** Their 1.0 is for a package that
  also reforms the base, removing the uplift at death, and includes an
  adjustment for shifting income between tax bases. Adopting it does not
  reproduce their revenue estimates.
- **No income tax is added back.** Shifting between gains and income is
  separate work
  ([#1982](https://github.com/PolicyEngine/policyengine-uk/issues/1982),
  [#1805](https://github.com/PolicyEngine/policyengine-uk/issues/1805)), and
  the central value already includes a cross-base adjustment.
- **The start date is a convention.** The value applies in every period. Its
  start date is the start of the model's timeline, not a change in law.

For a marginal rate on gains rising from 24% to 45%, the default scales
realised gains by $0.55 / 0.76 \approx 0.7237$. A marginal tax rate
elasticity of $-0.7$, a different convention, gives
$(0.45 / 0.24)^{-0.7} \approx 0.6440$: the two are not interchangeable.

```python
from policyengine_uk import Simulation

situation = {
    "people": {
        "person": {
            "age": {2026: 45},
            "employment_income": {2026: 100_000},
            "capital_gains": {2026: 200_000},
        }
    },
    "benunits": {"benunit": {"members": ["person"]}},
    "households": {"household": {"members": ["person"]}},
}
rates = {
    "gov.hmrc.cgt.higher_rate": {"2026": 0.45},
    "gov.hmrc.cgt.additional_rate": {"2026": 0.45},
}
reformed = Simulation(situation=situation, reform=rates)
# The marginal rate on the gains rises from 24% to 45%, so realised gains
# fall to 0.55 / 0.76 of £200,000, about £144,737.
print(reformed.calculate("capital_gains", 2026))
```

## When there is no response

- **No baseline.** A simulation built directly in policyengine-core (as the
  YAML tests are) has no baseline to compare with.
- **No elasticity.** The static settings below switch the response off.
- **The baseline's rules.** A simulation built without a reform, every branch
  of it, a reform's own baseline, and a reform that changes only the
  behavioural response settings all apply their baseline's rules. Their rates
  would be equal, so nothing is measured.
- **No gains.** Where no one has gains or losses, nothing is measured.

The response answers changes in the rules. A simulation whose inputs change
while its rules don't has no response. Marginal tax rates on earnings hold
realised gains at the simulation's own values: a pay rise is not a reform for
the response to answer.

Rules changed after a simulation is built count too. A simulation built
without a reform keeps a copy of itself, taken when it was built, as its
baseline. If a modifier then edits its parameters, it responds against that
copy.

## Other assumptions

Every setting is an ordinary parameter, so a reform or scenario can change it
for the years it covers. A reform dict's year key, such as `"2026"`, covers
that fiscal year only; `"2000-01-01.2100-12-31"` covers every year.

```python
RESPONSES = "gov.simulation.capital_gains_responses"
EVERY_YEAR = "2000-01-01.2100-12-31"

# Static: no response.
static = {
    f"{RESPONSES}.elasticity": {EVERY_YEAR: 0},
    f"{RESPONSES}.mtr_elasticity": {EVERY_YEAR: 0},
    f"{RESPONSES}.separate_badr_elasticity": {EVERY_YEAR: False},
}
# CenTax's sensitivities, or any other value.
lower = {f"{RESPONSES}.elasticity": {"2026": 0.5}}
upper = {f"{RESPONSES}.elasticity": {"2026": 2.0}}
# The OBR's elasticities: 3.6 for main-rate gains and badr_elasticity's 1.4
# for qualifying gains. This compares elasticities, not the OBR's full
# costing, which includes further effects.
obr = {
    f"{RESPONSES}.elasticity": {"2026": 3.6},
    f"{RESPONSES}.separate_badr_elasticity": {"2026": True},
}
static_costing = Simulation(situation=situation, reform={**rates, **static})
```

### The marginal tax rate convention

`gov.simulation.capital_gains_responses.mtr_elasticity` scales gains by
$(t_1 / t_0)^{e}$ instead, and can't be combined with a retention-rate
elasticity in the same period.

- **The default gives way.** Where the retention-rate settings keep their
  defaults, an MTR elasticity applies alone in its periods and the
  retention-rate elasticities count as zero. A `CapitalGainsResponseWarning`
  says so, once per tax-benefit system and period.
- **Silencing the warning.** Setting the retention-rate elasticity to 0 for
  the same periods gives the same results without the warning.
- **Conflicts raise.** A retention-rate elasticity changed to a nonzero value
  raises a `ValueError` alongside an MTR elasticity, as does a separate
  relief elasticity.
- **An explicit 1.** A retention-rate elasticity set to its default of 1
  can't be told apart from the default, so it resolves in the same way.

```python
legacy = {f"{RESPONSES}.mtr_elasticity": {"2026": -0.7}}
# Warns: the retention-rate default counts as zero in 2026.
with_warning = Simulation(situation=situation, reform={**rates, **legacy})
# The same results, without the warning.
explicit = {**legacy, f"{RESPONSES}.elasticity": {"2026": 0}}
without_warning = Simulation(situation=situation, reform={**rates, **explicit})
```

## The assumption a simulation applies

`capital_gains_response_assumption` resolves a simulation's settings for a
year as the response does, after every reform and modifier applied so far.
Its `to_dict()` gives the convention, the elasticities for main-rate and
qualifying gains, the MTR elasticity, the separate relief switch, and whether
each is the default, an override or set to zero for an MTR elasticity. It is
there to record with a run's results.

```python
from policyengine_uk.utils.capital_gains import capital_gains_response_assumption

print(capital_gains_response_assumption(reformed, 2026).to_dict())
```

## Moving from the static default

The elasticity used to default to 0, so CGT reforms were costed statically
unless a caller set an elasticity.

- **Static results.** Set the static settings above for the years you run.
- **MTR elasticity alone.** Results are unchanged, with a warning. Set the
  retention-rate elasticity to 0 to silence it.
- **Revenue.** Realised gains are part of household income. With a response,
  the change in household net income no longer equals the change in revenue,
  so use `gov_balance` for reforms that move the tax on gains.

## Runtime

A reform that changes the rules measures two marginal rates on gains per
simulation and year: one for the reform and one for its baseline. Each
recalculates household net income in branches of the simulation. Simulations
without a reform, baselines, reforms to the behavioural settings alone, and
populations without gains skip the measurement.
