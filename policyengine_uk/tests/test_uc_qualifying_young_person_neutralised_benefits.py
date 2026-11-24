"""The UC qualifying young person test under reforms that neutralise a benefit.

The Secretary of State excludes a person entitled to an existing benefit
from the UC qualifying young person test (SI 2014/1230 regs. 2(1) and 28).
A reform that neutralises a benefit's variable abolishes that benefit, so
nobody can be entitled to it and reg. 28 can't exclude on it. The predicate
checks each report against its own variable:

- Income Support: ``income_support``;
- income-based JSA: ``jsa_income``;
- income-related ESA: ``esa_income``;
- Housing Benefit: ``housing_benefit``;
- Child Tax Credit: ``child_tax_credit`` or ``tax_credits``;
- Working Tax Credit: ``working_tax_credit`` or ``tax_credits``.

The model pays all six in 2024, so the tests read 2024 unless they name
another year.
"""

import pytest
from policyengine_core.reforms import Reform

from policyengine_uk import Simulation

PREDICATE = "is_qualifying_young_person_for_universal_credit"
# Each report, and the variables whose neutralisation lifts its exclusion.
ROWS = {
    "income_support_reported": {"income_support"},
    "jsa_income_reported": {"jsa_income"},
    "esa_income_reported": {"esa_income"},
    "housing_benefit_reported": {"housing_benefit"},
    "child_tax_credit_reported": {"child_tax_credit", "tax_credits"},
    "working_tax_credit_reported": {"working_tax_credit", "tax_credits"},
}
NEUTRALISED = sorted(set().union(*ROWS.values()))


def neutralising(*names):
    class neutralise(Reform):
        def apply(self):
            for name in names:
                self.neutralize_variable(name)

    return neutralise


def young_people(reports, year, reform=None, amount=3_000):
    """One household per report: a parent aged 45 and a 17-year-old on a
    non-advanced course who reports that benefit (£3,000 a year unless the
    test says otherwise). North East, owned outright, no income."""
    people, benunits, households = {}, {}, {}
    for index, report in enumerate(reports):
        parent, young = f"parent_{index}", f"young_{index}"
        people[parent] = {
            "age": {year: 45},
            "is_parent": {year: True},
            "is_claimant_or_partner": {year: True},
        }
        people[young] = {
            "age": {year: 17},
            "current_education": {year: "POST_SECONDARY"},
            "is_claimant_or_partner": {year: False},
            report: {year: amount},
        }
        benunits[f"benunit_{index}"] = {"members": [parent, young]}
        households[f"household_{index}"] = {
            "members": [parent, young],
            "region": {year: "NORTH_EAST"},
            "tenure_type": {year: "OWNED_OUTRIGHT"},
        }
    return Simulation(
        situation={"people": people, "benunits": benunits, "households": households},
        reform=reform,
    )


def young_flags(sim, year):
    return sim.calculate(PREDICATE, year)[1::2].tolist()


def parent_awards(sim, year):
    return [round(float(x), 2) for x in sim.calculate("universal_credit", year)]


@pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
@pytest.mark.parametrize("neutralised", [None] + NEUTRALISED)
def test_a_reform_lifts_only_the_exclusions_on_the_benefit_it_neutralises(
    neutralised,
):
    year = 2024
    reform = neutralising(neutralised) if neutralised else None
    sim = young_people(list(ROWS), year, reform)
    expected = [neutralised in variables for variables in ROWS.values()]
    assert young_flags(sim, year) == expected


@pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
@pytest.mark.parametrize("neutralised", [None] + NEUTRALISED)
def test_a_reform_lifts_a_couples_tax_credit_exclusion_credit_by_credit(
    neutralised,
):
    """Two 18-year-olds on non-advanced courses form a couple, and the
    partner reports the couple's Child Tax Credit or Working Tax Credit
    award (Tax Credits Act 2002 s.3(3)(a)). The couple doesn't claim
    Universal Credit, so no claim ends its Child Tax Credit."""
    year = 2024
    people, benunits, households = {}, {}, {}
    credits = ("child_tax_credit_reported", "working_tax_credit_reported")
    for index, report in enumerate(credits):
        claimant, partner = f"claimant_{index}", f"partner_{index}"
        for name in (claimant, partner):
            people[name] = {
                "age": {year: 18},
                "current_education": {year: "UPPER_SECONDARY"},
                "is_claimant_or_partner": {year: True},
            }
        people[partner][report] = {year: 1_000}
        benunits[f"benunit_{index}"] = {
            "members": [claimant, partner],
            "would_claim_uc": {year: False},
        }
        households[f"household_{index}"] = {"members": [claimant, partner]}
    sim = Simulation(
        situation={"people": people, "benunits": benunits, "households": households},
        reform=neutralising(neutralised) if neutralised else None,
    )
    lifted = [neutralised in ROWS[report] for report in credits]
    expected = [flag for flag in lifted for _ in range(2)]
    assert sim.calculate(PREDICATE, year).tolist() == expected


@pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
def test_neutralising_child_tax_credit_alone_leaves_a_working_tax_credit_exclusion():
    year = 2024
    credits = ["child_tax_credit_reported", "working_tax_credit_reported"]
    alone = young_people(credits, year, neutralising("child_tax_credit"))
    both = young_people(credits, year, neutralising("tax_credits"))
    assert young_flags(alone, year) == [True, False]
    assert young_flags(both, year) == [True, True]


@pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
def test_neutralising_housing_benefit_restores_an_own_housing_benefit_young_person():
    """Household G: the 17-year-old reports their own Housing Benefit in 2026."""
    year = 2026
    kept = young_people(["housing_benefit_reported"], year)
    removed = young_people(
        ["housing_benefit_reported"], year, neutralising("housing_benefit")
    )
    assert young_flags(kept, year) == [False]
    assert young_flags(removed, year) == [True]
    assert parent_awards(kept, year)[0] == pytest.approx(5_098.80)
    assert parent_awards(removed, year)[0] == pytest.approx(9_321.36)


@pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
def test_neutralising_child_tax_credit_restores_an_own_child_tax_credit_young_person():
    """Household D: the 17-year-old reports their own Child Tax Credit in
    2024, £1,000."""
    year = 2024
    sims = {}
    for name, reform in (
        ("kept", None),
        ("child_tax_credit", neutralising("child_tax_credit")),
        ("tax_credits", neutralising("tax_credits")),
    ):
        sims[name] = young_people(
            ["child_tax_credit_reported"], year, reform, amount=1_000
        )
    assert young_flags(sims["kept"], year) == [False]
    assert parent_awards(sims["kept"], year)[0] == pytest.approx(4_721.40)
    for name in ("child_tax_credit", "tax_credits"):
        assert young_flags(sims[name], year) == [True]
        assert parent_awards(sims[name], year)[0] == pytest.approx(8_721.36)
