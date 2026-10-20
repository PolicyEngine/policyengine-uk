"""Property-based tests for cliff_evaluated.

marginal_tax_rate perturbs the employment income of adults 1 to N in each
household, where N is gov.simulation.marginal_tax_rate_adults, and leaves
everyone else's rate at zero. cliff_evaluated flags exactly those people. For
any household composition and any N:

1. Nobody under 18 is evaluated.
2. Each household has min(N, number of adults) evaluated members.
3. Evaluation goes to the oldest adults: no unevaluated adult is older than an
   evaluated adult in the same household.
4. Consistency with marginal_tax_rate: anyone not evaluated has a zero
   marginal tax rate and a zero cliff gap.
"""

from functools import lru_cache

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from policyengine_core.reforms import Reform, set_parameter
from policyengine_core.simulations import SimulationBuilder

from policyengine_uk import CountryTaxBenefitSystem

MTR_ADULTS = "gov.simulation.marginal_tax_rate_adults"
PROPERTY_SETTINGS = settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


@lru_cache(maxsize=None)
def tax_benefit_system(mtr_adults):
    modifier = set_parameter(
        MTR_ADULTS, mtr_adults, return_modifier=True, period="year:2000:100"
    )

    class override(Reform):
        def apply(self):
            self.parameters = modifier(self.parameters)

    return override(CountryTaxBenefitSystem())


earnings = st.sampled_from([0, 5_000, 20_000, 60_000, 120_000])


@st.composite
def households(draw):
    # A family benefit unit of up to two adults and some children, plus up to
    # two other adults in their own benefit units.
    family_adults = draw(st.lists(st.integers(18, 90), max_size=2))
    children = draw(st.lists(st.integers(0, 17), max_size=4))
    other_adults = draw(st.lists(st.integers(18, 90), max_size=2))
    if not family_adults and not children and not other_adults:
        children = [draw(st.integers(0, 17))]
    return dict(
        family_adults=[(age, draw(earnings)) for age in family_adults],
        children=children,
        other_adults=[(age, draw(earnings)) for age in other_adults],
    )


@st.composite
def scenarios(draw):
    return dict(
        mtr_adults=draw(st.integers(0, 3)),
        households=draw(st.lists(households(), min_size=1, max_size=4)),
    )


def simulate(scenario, year=2025):
    people, benunits, households_ = {}, {}, {}
    household_of = []
    for h, household in enumerate(scenario["households"]):
        members, family = [], []
        for a, (age, income) in enumerate(household["family_adults"]):
            name = f"h{h}_family_adult_{a}"
            people[name] = {"age": age, "employment_income": income}
            family.append(name)
        for c, age in enumerate(household["children"]):
            name = f"h{h}_child_{c}"
            people[name] = {"age": age}
            family.append(name)
        if family:
            benunits[f"h{h}_family"] = {"members": family}
        members += family
        for a, (age, income) in enumerate(household["other_adults"]):
            name = f"h{h}_other_adult_{a}"
            people[name] = {"age": age, "employment_income": income}
            benunits[name] = {"members": [name]}
            members.append(name)
        households_[f"h{h}"] = {"members": members}
        household_of += [h] * len(members)
    builder = SimulationBuilder()
    builder.set_default_period(year)
    sim = builder.build_from_dict(
        tax_benefit_system(scenario["mtr_adults"]),
        {"people": people, "benunits": benunits, "households": households_},
    )
    values = {
        variable: np.asarray(sim.calculate(variable, year))
        for variable in [
            "age",
            "cliff_evaluated",
            "marginal_tax_rate",
            "cliff_gap",
        ]
    }
    values["household"] = np.array(household_of)
    return values


@PROPERTY_SETTINGS
@given(scenarios())
def test_cliff_evaluated_matches_simulated_adults(scenario):
    values = simulate(scenario)
    evaluated = values["cliff_evaluated"]
    age = values["age"]
    adult = age >= 18

    # 1. Nobody under 18 is evaluated.
    assert not (evaluated & ~adult).any()

    for h in np.unique(values["household"]):
        in_household = values["household"] == h
        # 2. min(N, adults) evaluated members per household.
        assert evaluated[in_household].sum() == min(
            scenario["mtr_adults"], adult[in_household].sum()
        )
        # 3. The evaluated adults are the oldest.
        evaluated_ages = age[in_household & evaluated]
        unevaluated_adult_ages = age[in_household & adult & ~evaluated]
        if len(evaluated_ages) and len(unevaluated_adult_ages):
            assert unevaluated_adult_ages.max() <= evaluated_ages.min()

    # 4. Unevaluated people have no simulated marginal tax rate or cliff gap.
    assert (values["marginal_tax_rate"][~evaluated] == 0).all()
    assert (values["cliff_gap"][~evaluated] == 0).all()
