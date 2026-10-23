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
wages only.
"""

from pathlib import Path

import pytest
import yaml

from policyengine_uk import Simulation

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
