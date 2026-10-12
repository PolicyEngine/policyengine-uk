"""Property-based tests for the Universal Credit two-child limit age exemption.

The contrib reform gov.contrib.two_child_limit.age_exemption.universal_credit
exempts a benefit unit from the two-child limit when any member is younger
than the threshold age. For any family, year and positive threshold:

1. Differential: an exempt family's uc_individual_child_element equals its
   value with the two-child limit repealed (limit.child_count = inf); a
   non-exempt family's equals its baseline value.
2. The exemption only adds standard child elements: for every person the
   reformed element minus the baseline element is either zero or the monthly
   child element times 12. In particular it never lowers anyone's element and
   never switches the higher first-child amount on or off, since that amount
   depends on a birth before 6 April 2017, not on the exemption.
"""

from functools import lru_cache

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from policyengine_core.reforms import Reform, set_parameter
from policyengine_core.simulations import SimulationBuilder

from policyengine_uk import CountryTaxBenefitSystem

AGE_EXEMPTION = "gov.contrib.two_child_limit.age_exemption.universal_credit"
CHILD_LIMIT = "gov.dwp.universal_credit.elements.child.limit.child_count"
# The two-child limit applies from April 2017 and is repealed from April 2026;
# 2026 checks that the exemption is inert once there is no limit.
YEARS = list(range(2018, 2027))
PROPERTY_SETTINGS = settings(
    max_examples=60,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
TOLERANCE = 0.01


@lru_cache(maxsize=None)
def tax_benefit_system(parameter, value):
    """The UK system, with one parameter overridden for all years if given."""
    system = CountryTaxBenefitSystem()
    if parameter is None:
        return system
    modifier = set_parameter(
        parameter, value, return_modifier=True, period="year:2000:100"
    )

    class override(Reform):
        def apply(self):
            self.parameters = modifier(self.parameters)

    return override(system)


@st.composite
def families(draw):
    adults = draw(st.lists(st.integers(18, 60), min_size=1, max_size=2))
    children = draw(
        st.lists(
            st.tuples(st.integers(0, 19), st.booleans()),
            min_size=0,
            max_size=6,
        )
    )
    return adults, children


@st.composite
def scenarios(draw):
    return dict(
        year=draw(st.sampled_from(YEARS)),
        threshold=draw(st.integers(1, 19)),
        families=draw(st.lists(families(), min_size=1, max_size=8)),
    )


def build_situation(scenario):
    year = scenario["year"]
    people, benunits, households = {}, {}, {}
    for f, (adults, children) in enumerate(scenario["families"]):
        members = []
        for a, age in enumerate(adults):
            name = f"f{f}_adult_{a}"
            people[name] = {"age": {year: age}}
            members.append(name)
        for c, (age, in_education) in enumerate(children):
            name = f"f{f}_child_{c}"
            people[name] = {
                "age": {year: age},
                "is_in_non_advanced_education": {year: in_education},
            }
            members.append(name)
        benunits[f"b{f}"] = {"members": members, "would_claim_uc": {year: True}}
        households[f"h{f}"] = {"members": members}
    return {"people": people, "benunits": benunits, "households": households}


def child_elements(scenario, parameter=None, value=None):
    system = tax_benefit_system(parameter, value)
    builder = SimulationBuilder()
    builder.set_default_period(scenario["year"])
    sim = builder.build_from_dict(system, build_situation(scenario))
    return np.asarray(sim.calculate("uc_individual_child_element", scenario["year"]))


def family_is_exempt(scenario):
    """Per person: whether any member of their benefit unit is under the threshold."""
    exempt = []
    for adults, children in scenario["families"]:
        ages = list(adults) + [age for age, _ in children]
        family_exempt = any(age < scenario["threshold"] for age in ages)
        exempt += [family_exempt] * len(ages)
    return np.array(exempt, dtype=bool)


@PROPERTY_SETTINGS
@given(scenarios())
def test_age_exemption_lifts_only_the_two_child_limit(scenario):
    baseline = child_elements(scenario)
    repealed = child_elements(scenario, CHILD_LIMIT, np.inf)
    reformed = child_elements(scenario, AGE_EXEMPTION, scenario["threshold"])

    # 1. Exempt families are paid as if the limit were repealed; others are
    # unaffected.
    expected = np.where(family_is_exempt(scenario), repealed, baseline)
    np.testing.assert_allclose(reformed, expected, atol=TOLERANCE)

    # 2. Each person's element either stays the same or gains one standard
    # child element.
    child = (
        tax_benefit_system(None, None)
        .parameters(f"{scenario['year']}-01-01")
        .gov.dwp.universal_credit.elements.child
    )
    # The property only distinguishes the two amounts while they differ.
    assert child.first.higher_amount != child.amount
    increase = reformed - baseline
    no_change = np.abs(increase) <= TOLERANCE
    one_standard_element = np.abs(increase - child.amount * 12) <= TOLERANCE
    unexpected = ~(no_change | one_standard_element)
    assert not unexpected.any(), (
        f"Unexpected child element changes: {increase[unexpected]}"
    )
