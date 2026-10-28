"""Every source in the Childcare Offer for Wales gross income lists counts
towards the £100,000 limit.

The limit counts all of a parent's income (guidance para 69; July 2020 income
guidance, questions 8 and 9), so adding any listed source can only take a
parent over it, never back under. A lone parent with £99,000 of wages
qualifies; £1,001 more of any listed source, whether the parent or the benefit
unit holds it, takes them to £100,001 and over the limit. Child Benefit, which
the model otherwise pays for the child, is set to zero so that each source
alone decides the result.

One simulation holds a family for each source, plus a control family with
wages only. The cases come from the lists, so a source removed from a list
would just lose its case; the lists are also pinned to the reviewed sources
below, so a removal fails here too. Each source is also checked not to add
another listed source (through adds or subtracts, at any depth), which would
count it twice, and the sources are checked to expand to disjoint variables.
Those checks do not see a formula that reads another listed source.
"""

from pathlib import Path

import pytest
import yaml
from policyengine_core.parameters import get_parameter

from policyengine_uk import Simulation
from policyengine_uk.system import system

YEAR = 2026
WAGES = 99_000
EXTRA = 1_001
# A 3-year-old using all 30 hours: (20 x 39 + 30 x 9) x £6.67.
FUNDED = 7_003.50
INCOME = (
    Path(__file__).parents[1]
    / "parameters"
    / "gov"
    / "welsh_government"
    / "childcare_offer"
    / "income"
)


def sources(name):
    values = yaml.safe_load((INCOME / f"{name}.yaml").read_text())["values"]
    return values[max(values)]


CASES = [("people", source) for source in sources("gross_income_sources")] + [
    ("benunits", source) for source in sources("benunit_gross_income_sources")
]

# The sources as reviewed. Adding a source to a list, or removing one, means
# changing it here too.
REVIEWED = {
    "gross_income_sources": {
        "employment_income",
        "employment_benefits",
        "pension_contributions_via_salary_sacrifice_from_pay",
        "self_employment_income",
        "private_pension_income",
        "social_security_income",
        "pip",
        "dla",
        "attendance_allowance",
        "iidb",
        "sda",
        "maternity_allowance",
        "afcs",
        "war_widows_pension",
        "armed_forces_independence_payment",
        "bsp",
        "winter_fuel_payment",
        "private_transfer_income",
        "adult_ema",
        "access_fund",
        "education_grants",
        "parents_learning_allowance",
        "adult_dependants_grant",
        "property_income",
        "sublet_income",
        "savings_interest_income",
        "other_investment_income",
        "dividend_income",
        "taxable_miscellaneous_income",
        "maintenance_income",
        "spousal_maintenance_income",
    },
    "benunit_gross_income_sources": {
        "child_benefit",
        "universal_credit",
        "child_tax_credit",
        "working_tax_credit",
        "housing_benefit",
        "income_support",
        "pension_credit",
        "esa_income",
        "jsa_income",
    },
}


def components(name):
    """Every variable that `name` adds or subtracts, at any depth."""
    variable = system.variables[name]
    found = set()
    for terms in (variable.adds, variable.subtracts):
        if isinstance(terms, str):
            terms = get_parameter(system.parameters, terms)(f"{YEAR}-01-01")
        for term in terms or []:
            if term in system.variables:
                found |= {term} | components(term)
    return found


@pytest.fixture(scope="module")
def offer():
    situation = {"people": {}, "benunits": {}, "households": {}}
    for i, case in enumerate([None] + CASES):
        parent = {"age": {YEAR: 30}, "employment_income": {YEAR: WAGES}}
        benunit = {"child_benefit": {YEAR: 0}}
        if case is not None:
            entity, source = case
            holder = parent if entity == "people" else benunit
            holder[source] = {YEAR: holder.get(source, {YEAR: 0})[YEAR] + EXTRA}
        members = [f"parent_{i}", f"child_{i}"]
        situation["people"][members[0]] = parent
        situation["people"][members[1]] = {"age": {YEAR: 3}}
        situation["benunits"][f"benunit_{i}"] = {"members": members, **benunit}
        situation["households"][f"household_{i}"] = {
            "members": members,
            "region": {YEAR: "WALES"},
        }
    simulation = Simulation(situation=situation)
    return simulation.calculate("wales_childcare_offer", YEAR)


def test_wages_alone_are_within_the_limit(offer):
    assert offer[0] == pytest.approx(FUNDED, abs=0.01)


@pytest.mark.parametrize("entity, source", CASES, ids=[source for _, source in CASES])
def test_each_listed_source_counts_towards_the_limit(offer, entity, source):
    assert offer[1 + CASES.index((entity, source))] == 0


@pytest.mark.parametrize("name", sorted(REVIEWED))
def test_each_list_holds_the_reviewed_sources_once(name):
    listed = sources(name)
    assert len(listed) == len(set(listed))
    assert set(listed) == REVIEWED[name]


@pytest.mark.parametrize("entity, source", CASES, ids=[source for _, source in CASES])
def test_no_listed_source_adds_another(entity, source):
    listed = {other for _, other in CASES}
    assert not components(source) & listed


def test_listed_sources_expand_to_disjoint_variables():
    # Each source's closure is the source and every variable it adds or
    # subtracts, at any depth. Overlapping closures would count the shared
    # income twice, even where neither source adds the other.
    closures = {source: {source} | components(source) for _, source in CASES}
    overlaps = {
        (first, second): sorted(closures[first] & closures[second])
        for i, first in enumerate(closures)
        for second in list(closures)[i + 1 :]
        if closures[first] & closures[second]
    }
    assert len(closures) == 40
    assert not overlaps, overlaps
