"""The benefit cap reads the couple's held income-related ESA and income-based
JSA under gov.contrib.policyengine.disable_simulated_benefits.

The reform holds esa_income and jsa_income at the dataset year's reported
total for ten years, while the reports are uprated, and sets the claimant's
and partner's part (claimant_or_partner_esa_income,
claimant_or_partner_jsa_income) from their own reports. In a later year the
held total matches neither reading award_of_members makes of a stored award
(the award on everyone's reports, or their plain total), so it took all of
it to be the couple's. The benefit cap's readers called award_of_members on
esa_income and jsa_income, so another member's held award (a non-dependent
adult's, claimed in their own right) raised the cap's total of welfare
benefits, and lifted the cap for a claimant with an ESA support component
who receives no ESA (review r11 on #2075). They now read award_of_couple.

Invariants:

1. Metamorphic, reform on: where the cap's couple is the claimant and
   partner, in each of the reform's years, the cap's total, both schemes'
   specified-benefit exemptions and both reductions are the same whether or
   not a member outside the couple reports ESA or JSA in the dataset year.
2. Differential, reform off: the cap's total equals the code it replaces
   (policyengine-uk main at b4dbaf57a) to within a penny, and the couple's
   award the exemptions read equals award_of_members for the couple, except
   that an award within half a penny of zero is none.
3. For a couple that is not the claimant and partner, award_of_couple is
   award_of_members for that couple.
4. A claimant-or-partner award entered directly reaches the cap.
"""

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st
from policyengine_core.periods import period as as_period

from policyengine_uk import Simulation
from policyengine_uk.tests.test_income_support_eligibility_properties import (
    DIFFERENTIAL_SETTINGS,
    FAMILIES,
    input_settings,
    situation as property_situation,
)
from policyengine_uk.utils.benefit_cap import benefit_cap_couple
from policyengine_uk.utils.benefit_unit import (
    HALF_PENNY,
    add_for_members,
    award_of_couple,
    award_of_members,
)
from policyengine_uk.utils.scenario import Scenario
from policyengine_uk.variables.gov.dwp.benefit_cap_welfare_benefits import (
    CLAIMANT_OR_PARTNER_BENEFITS,
    FAMILY_BENEFITS,
)
from policyengine_uk.variables.gov.dwp.esa_income import income_related_esa_award
from policyengine_uk.variables.gov.dwp.jsa_income import income_related_jsa_award

REFORM_ON = Scenario(
    applied_before_data_load=True,
    parameter_changes={"gov.contrib.policyengine.disable_simulated_benefits": True},
)
YEARS = [2025, 2026, 2027]
CAP = [
    "benefit_cap_welfare_benefits",
    "is_uc_benefit_cap_exempt_specified_benefit",
    "is_housing_benefit_benefit_cap_exempt_specified_benefit",
    "uc_benefit_cap_reduction",
    "housing_benefit_benefit_cap_reduction",
    "benefit_cap_reduction",
]
AWARDS = {
    "esa_income": ("esa_income_reported", income_related_esa_award),
    "jsa_income": ("jsa_income_reported", income_related_jsa_award),
}


def in_each_year(value):
    return {year: value for year in YEARS}


def cap_families(support_component):
    """Four benefit units in London, each a claimant of 40 and another
    adult of 30 outside the couple who claims in their own right. Two have
    £25,000 of Universal Credit before the cap, two £25,000 of Housing
    Benefit before the cap, so each is capped (the London cap for a single
    claimant without children is below £25,000). In one of each pair the
    other adult reports £3,000 of ESA and £2,000 of JSA in 2025; in the
    control they report none. The claimant reports no ESA, and has an ESA
    support component when support_component is true, so only a misread
    ESA award would exempt them."""
    people, benunits, households = {}, {}, {}
    for scheme in ("uc", "hb"):
        for other_reports in (False, True):
            unit = f"{scheme}_{'other_reports' if other_reports else 'control'}"
            members = [f"{unit}_claimant", f"{unit}_other"]
            for member, is_claimant in zip(members, (True, False)):
                reports = other_reports and not is_claimant
                people[member] = {
                    "age": in_each_year(40 if is_claimant else 30),
                    "is_claimant_or_partner": in_each_year(is_claimant),
                    "is_uc_claimant": in_each_year(is_claimant),
                    "current_education": in_each_year("NOT_IN_EDUCATION"),
                    "esa_includes_support_component": in_each_year(
                        support_component and is_claimant
                    ),
                    "esa_income_reported": {2025: 3_000 if reports else 0},
                    "jsa_income_reported": {2025: 2_000 if reports else 0},
                }
            benunits[unit] = {
                "members": members,
                "esa_income_assessable_capital": in_each_year(0),
                "jsa_income_assessable_capital": in_each_year(0),
                "universal_credit_pre_benefit_cap": in_each_year(
                    25_000 if scheme == "uc" else 0
                ),
                "housing_benefit_pre_benefit_cap": in_each_year(
                    25_000 if scheme == "hb" else 0
                ),
                "uc_LCWRA_element": in_each_year(0),
                "uc_carer_element": in_each_year(0),
                "uc_childcare_element": in_each_year(0),
            }
            households[unit] = {"members": members, "region": in_each_year("LONDON")}
    return {"people": people, "benunits": benunits, "households": households}


UNITS = ["uc_control", "uc_other_reports", "hb_control", "hb_other_reports"]


def by_unit(simulation, variable, year):
    return dict(zip(UNITS, np.asarray(simulation.calculate(variable, year)).tolist()))


@pytest.mark.parametrize("support_component", [False, True])
def test_another_members_held_award_never_enters_the_benefit_cap(support_component):
    simulation = Simulation(
        situation=cap_families(support_component), scenario=REFORM_ON
    )
    for year in YEARS:
        # The reform holds the other adult's awards in every year, and the
        # couple's own awards are nil.
        esa = by_unit(simulation, "esa_income", year)
        assert esa["uc_other_reports"] == esa["hb_other_reports"] == 3_000
        for name in [
            "claimant_or_partner_esa_income",
            "claimant_or_partner_jsa_income",
        ]:
            assert set(by_unit(simulation, name, year).values()) == {0}, (name, year)
        for name in CAP:
            values = by_unit(simulation, name, year)
            for scheme in ("uc", "hb"):
                assert (
                    values[f"{scheme}_other_reports"] == values[f"{scheme}_control"]
                ), (name, year, scheme, values)
        # The cap bites in every family: no misread award lifts it.
        reductions = by_unit(simulation, "benefit_cap_reduction", year)
        assert all(reduction > 0 for reduction in reductions.values()), (
            year,
            reductions,
        )


def replaced_benefit_cap_welfare_benefits(benunit, period):
    """benefit_cap_welfare_benefits at policyengine-uk main b4dbaf57a
    (comments removed)."""
    couple = benefit_cap_couple(benunit, period)
    income_based = award_of_members(
        benunit,
        period,
        "jsa_income",
        "jsa_income_reported",
        income_related_jsa_award,
        couple,
    ) + award_of_members(
        benunit,
        period,
        "esa_income",
        "esa_income_reported",
        income_related_esa_award,
        couple,
    )
    return income_based + add_for_members(
        benunit, period, CLAIMANT_OR_PARTNER_BENEFITS + FAMILY_BENEFITS, couple
    )


@DIFFERENTIAL_SETTINGS
@given(FAMILIES, st.data())
def test_the_benefit_cap_matches_the_replaced_readers_with_the_reform_off(drawn, data):
    capital_as_savings, esa_income, jsa_income = data.draw(input_settings(len(drawn)))
    units = [(*family, extra) for family, extra in drawn]
    simulation = Simulation(
        situation=property_situation(units, capital_as_savings, esa_income, jsa_income)
    )
    period = as_period(2025)
    benunit = simulation.populations["benunit"]
    np.testing.assert_allclose(
        simulation.calculate("benefit_cap_welfare_benefits", 2025),
        replaced_benefit_cap_welfare_benefits(benunit, period),
        rtol=0,
        atol=2 * HALF_PENNY,
    )
    # The couple's award as the specified-benefit exemptions read it, for
    # the claimant and partner (Housing Benefit) and the benefit cap's
    # couple (Universal Credit).
    couples = [
        benunit.members("is_claimant_or_partner", period),
        benefit_cap_couple(benunit, period),
    ]
    for award, (reported, award_on_reports) in AWARDS.items():
        stored = benunit(award, period)
        for couple in couples:
            replaced = award_of_members(
                benunit, period, award, reported, award_on_reports, couple
            )
            switched = award_of_couple(
                benunit, period, award, reported, award_on_reports, couple
            )
            np.testing.assert_array_equal(
                switched,
                np.where((stored > HALF_PENNY) & (replaced > HALF_PENNY), replaced, 0),
            )


def test_a_couple_that_is_not_the_claimant_and_partner_reads_the_stored_award():
    """A couple of whom only the claimant is in the rule's couple (as for a
    Universal Credit claim where is_uc_claimant is entered for one member):
    the claimant-or-partner award is not that couple's, so award_of_couple
    reads the stored award by value, as award_of_members does."""
    simulation = Simulation(
        situation={
            "people": {
                "claimant": {"age": 40, "esa_income_reported": 3_000},
                "partner": {"age": 38, "esa_income_reported": 2_000},
            },
            # Not claiming Universal Credit, which would end the couple's
            # income-related ESA (esa_income_report_closed).
            "benunits": {
                "couple": {"members": ["claimant", "partner"], "would_claim_uc": False}
            },
            "households": {"home": {"members": ["claimant", "partner"]}},
        }
    )
    period = as_period(2025)
    benunit = simulation.populations["benunit"]
    claimant_only = np.array([True, False])
    for award, (reported, award_on_reports) in AWARDS.items():
        np.testing.assert_array_equal(
            award_of_couple(
                benunit, period, award, reported, award_on_reports, claimant_only
            ),
            award_of_members(
                benunit, period, award, reported, award_on_reports, claimant_only
            ),
        )
    # The two differ here: the claimant-or-partner award covers both.
    assert (
        simulation.calculate("claimant_or_partner_esa_income", 2025)[0]
        > (
            award_of_members(
                benunit,
                period,
                "esa_income",
                "esa_income_reported",
                income_related_esa_award,
                claimant_only,
            )[0]
        )
    )


@pytest.mark.parametrize("award", ["esa_income", "jsa_income"])
def test_an_entered_claimant_or_partner_award_reaches_the_benefit_cap(award):
    """An award entered for claimant_or_partner_* is the couple's award for
    the benefit cap too, as for the Income Support gate and the passports."""

    def total(entered):
        person = {"age": 40}
        unit = {"members": ["claimant"]}
        if entered is not None:
            unit[f"claimant_or_partner_{award}"] = entered
        simulation = Simulation(
            situation={
                "people": {"claimant": person},
                "benunits": {"family": unit},
                "households": {"home": {"members": ["claimant"]}},
            }
        )
        return simulation.calculate("benefit_cap_welfare_benefits", 2025)[0]

    assert total(5_000) - total(None) == pytest.approx(5_000, abs=0.01)
