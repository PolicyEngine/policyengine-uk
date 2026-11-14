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
the medium-term (five-year) effect of their reform package, with the range
they consider, 0.5 to 2.0, as sensitivities.

The assumption has limits:

- **For rate changes alone it is low.** Their starting point is about 1.5,
  Agersnap and Zidar's five-year estimate. They bring it down to 1.0 for
  their package's base changes, removing the uplift at death and charging
  gains on emigration, and because taxing gains and income alike moves
  income back from gains into income tax, which they count as revenue kept.
  They expect a reform without those base changes to have a higher
  elasticity, and so lower revenue (p. 37). PolicyEngine adds no income tax
  back, so for a reform to rates alone their reasoning points to a higher
  value, such as their unadjusted 1.5. The default then overstates what a
  rate rise raises. Adopting 1.0 does not reproduce their revenue estimates.
- **It is a medium-term value.** The studies behind it find larger responses
  soon after a reform: about 1.6 at three to five years (Agersnap and Zidar)
  and 1.8 in the first year for large gainers in Canada (Lavecchia and
  Tazhitdinova), much of it retiming (pp. 34–35). Forestalling before a
  reform isn't modelled either. A score for the first year after a reform is
  likely to understate the response.
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

### Large rate rises

With this response, the revenue from a single rate on gains peaks where the
rate is $1 / (1 + e)$: 50% at the default, 40% at 1.5, 33% at 2.0 and about
22% at the 3.6 of the OBR comparison below. So for a large rate rise the
elasticity can decide whether revenue rises or falls. In the example above,
the person's capital gains tax rises by £16,502 at the default and by £6,777
at 1.5, and falls by £20,536 at 3.6. Official costings can have the other
sign. As of 2024, HMRC's ready reckoner had a 10 percentage point rise in the
top rates raising over £5bn before behaviour, and losing £2bn a year by the
third year once behaviour is counted (Advani, Lonsdale and Summers 2024,
p. 33).

## What the response moves

- **Household incomes.** Realised gains are part of household market income.
  So the response moves household net income as well as the tax.
  - For a capital gains tax rise, net income falls by the tax plus the gains
    no longer realised. Those gains are deferred, not lost: the assets are
    still held.
  - In the example above, the person's net income falls by £71,765 with the
    response and £41,370 without it. Revenue rises by £16,502, not £41,370.
  - Per-household impacts, income deciles, and winners and losers all count
    the gains not realised as income lost.

  This was already true for anyone who set an elasticity; the default makes
  it the published figure. For revenue, use `gov_balance` or the tax
  variables, not the change in household net income. Whether distributional
  measures should use gains before the response is an open methodology
  question.
- **Reforms to other taxes.** Income tax bands and allowances decide which
  capital gains tax rate gains fall in. So a reform to them changes the rate
  on some people's gains, and their realisations respond.
  - With earnings of £30,000 and gains of £20,000, cutting the basic rate
    band to £20,000, or the personal allowance to £5,000, lowers realised
    gains by £1,463 (7.3%).
  - Costings that include capital gains tax, such as `gov_balance`, move with
    that response.

## When there is no response

- **No baseline.** A simulation built directly in policyengine-core (as the
  YAML tests are) has no baseline to compare with.
- **No elasticity.** The static settings below switch the response off.
- **The baseline's rules.** A simulation built without a reform, every branch
  of it, a reform's own baseline, and a reform that changes only the
  behavioural response settings all apply their baseline's rules. Their rates
  would be equal, so nothing is measured.
- **No gains.** Where no one has gains or losses, nothing is measured.
- **No change at the margin.** The response answers the rate on a person's
  last pound of gains. A reform to one band's rate does nothing for someone
  whose last pound falls in another band. Raising only the higher rate to 45%
  raises the example person's tax from £47,280 to £65,642 with no response,
  as their last pound of gains is taxed at the unchanged additional rate.

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

The response scales the gains already in the data, so it can't change their
level. A comparison in pounds with the OBR's costing therefore mixes the gap
between the elasticities with any gap in the level of gains and capital gains
tax.

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
- **Household and distributional results.** They now count gains no longer
  realised as income lost, and reforms to income tax bands and allowances move
  realised gains too (see [What the response moves](#what-the-response-moves)).

## Runtime

A reform that changes the rules measures two marginal rates on gains per
simulation and year: one for the reform and one for its baseline. Each
recalculates capital gains tax, and what it depends on, in branches of the
simulation; on the enhanced FRS that adds about two seconds per reformed
simulation and year. Simulations without a reform, baselines, reforms to the
behavioural settings alone, and populations without gains skip the
measurement.

The marginal rate on gains is the rise in capital gains tax per pound of
marginal gains. Realised gains reach household net income only as market
income and through that tax, so it is also the share of marginal gains net
income does not keep; a test checks that no other variable reads realised
gains.
