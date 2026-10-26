"""Separate preassessed ESA/JSA claims keep their own existing report screens.

The capital premise is the model's shared-benefit-unit proxy, not evidence of
an outside claimant's capital. SOURCE's ordinary £7,000 case has £4 weekly
capital income, £208 under the existing 52-week convention. A couple is one
claim; each outside reporter is a separate claim. No age/PC entitlement rule
or full award calculation is certified here.
"""

import pytest

from policyengine_uk import Simulation
from policyengine_uk.utils.scenario import Scenario

YEAR = 2025
AWARDS = ["esa_income", "jsa_income"]


def family(
    award,
    couple_report=3_000,
    outside_reports=(3_000,),
    couple_works=False,
    outside_works=None,
    capital=0,
    closed_outside=False,
    alternate_cap_couple=False,
    scenario=None,
):
    outside_works = outside_works or (False,) * len(outside_reports)
    people = {
        "claimant": {
            "age": 40,
            "is_claimant_or_partner": True,
            "receives_carer_benefit": True,
            "income_support_reported": 1_000,
            f"{award}_reported": couple_report,
            "esa_income_claimant_remunerative_work": couple_works,
            "jsa_remunerative_work_hours": 40 if couple_works else 0,
            "person_legacy_benefits_closed": False,
        }
    }
    for i, (report, works) in enumerate(zip(outside_reports, outside_works)):
        people[f"outside_{i}"] = {
            "age": 30,
            "is_claimant_or_partner": False,
            "current_education": "NOT_IN_EDUCATION",
            f"{award}_reported": report,
            "esa_income_claimant_remunerative_work": works,
            "jsa_remunerative_work_hours": 40 if works else 0,
            "person_legacy_benefits_closed": closed_outside,
        }
    if alternate_cap_couple:
        for name, person in people.items():
            person["is_uc_assessed_claimant"] = name == "outside_0"
    members = list(people)
    inputs = {
        "members": members,
        "would_claim_uc": {YEAR: False},
        "would_claim_pc": {YEAR: False},
        "income_support_assessable_capital": {YEAR: 0},
        f"{award}_assessable_capital": {YEAR: capital},
    }
    if alternate_cap_couple:
        inputs["universal_credit_pre_benefit_cap"] = {YEAR: 1}
    return Simulation(
        situation={
            "people": {
                name: {key: {YEAR: value} for key, value in person.items()}
                for name, person in people.items()
            },
            "benunits": {"family": inputs},
            "households": {"home": {"members": members}},
        },
        scenario=scenario,
    )


def amount(simulation, variable):
    return float(simulation.calculate(variable, YEAR)[0])


@pytest.mark.parametrize("award", AWARDS)
def test_working_outside_report_does_not_inflate_total(award):
    simulation = family(award, outside_works=(True,))
    assert amount(simulation, award) == 3_000
    assert amount(simulation, f"claimant_or_partner_{award}") == 3_000


@pytest.mark.parametrize("award", AWARDS)
def test_eligible_outside_report_survives_failed_couple(award):
    simulation = family(award, couple_works=True)
    assert amount(simulation, award) == 3_000
    assert amount(simulation, f"claimant_or_partner_{award}") == 0


@pytest.mark.parametrize("award", AWARDS)
@pytest.mark.parametrize(
    "couple_works,outside_works,total,couple",
    [
        (False, (False, False), 3_876, 2_792),
        (False, (False, True), 3_584, 2_792),
        (True, (False, False), 1_084, 0),
    ],
)
def test_outside_reports_each_apply_own_tariff_and_work(
    award, couple_works, outside_works, total, couple
):
    simulation = family(
        award,
        outside_reports=(1_000, 500),
        outside_works=outside_works,
        couple_works=couple_works,
        capital=7_000,
    )
    assert amount(simulation, award) == total
    assert amount(simulation, f"claimant_or_partner_{award}") == couple


@pytest.mark.parametrize("award", AWARDS)
def test_partitioned_formula_retains_couple_provenance(award):
    # The couple's £200 is extinguished by £832 tariff income. Only the
    # separate outside claim pays: 3,000 - 832 = 2,168. It cannot bar IS.
    simulation = family(award, couple_report=200, capital=10_000)
    assert amount(simulation, award) == 2_168
    assert amount(simulation, f"claimant_or_partner_{award}") == 0
    assert simulation.calculate("income_support_eligible", YEAR)[0]


@pytest.mark.parametrize("award", AWARDS)
def test_alternate_couple_scope_preserves_original_report_groups(award):
    # Selecting a working outside reporter as the cap's assessed UC person
    # must not move them into the original ESA/JSA claimant/partner group.
    with_report = family(
        award,
        outside_reports=(1_000,),
        outside_works=(True,),
        capital=7_000,
        alternate_cap_couple=True,
    )
    without_report = family(
        award,
        outside_reports=(0,),
        outside_works=(True,),
        capital=7_000,
        alternate_cap_couple=True,
    )
    assert amount(with_report, "benefit_cap_welfare_benefits") == amount(
        without_report, "benefit_cap_welfare_benefits"
    )


@pytest.mark.parametrize("award", AWARDS)
def test_closed_reports_and_inactive_jsa_are_not_paid(award):
    simulation = family(award, closed_outside=True)
    assert amount(simulation, award) == 3_000
    if award == "jsa_income":
        inactive = family(
            award,
            scenario=Scenario(parameter_changes={"gov.dwp.JSA.income.active": False}),
        )
        assert amount(inactive, award) == 0


def test_alternate_uc_claimant_mask_reaches_specified_benefit_exemption():
    """A supported UC claimant-mask override reaches the actual cap and final UC.

    The different masks exercise the callback interface, rather than assert
    a new entitlement rule for a couple claiming as a single person.
    """
    import math

    members = ["claimant", "partner"]
    people = {}
    for name in members:
        people[name] = {
            "age": {YEAR: 40},
            "is_claimant_or_partner": {YEAR: True},
            "is_uc_claimant": {YEAR: name == "claimant"},
            "current_education": {YEAR: "NOT_IN_EDUCATION"},
            "employment_income": {YEAR: 0},
            "esa_income_reported": {YEAR: 0},
            "esa_contrib_reported": {YEAR: 0},
            "care_hours": {YEAR: 0},
            "is_disabled_for_benefits": {YEAR: False},
        }
    simulation = Simulation(
        situation={
            "people": people,
            "benunits": {
                "family": {
                    "members": members,
                    "would_claim_uc": {YEAR: True},
                    "would_claim_pc": {YEAR: False},
                    "working_tax_credit": {YEAR: 0},
                }
            },
            "households": {
                "home": {
                    "members": members,
                    "region": {YEAR: "NORTH_EAST"},
                    "country": {YEAR: "ENGLAND"},
                }
            },
        }
    )
    assert simulation.calculate("is_claimant_or_partner", YEAR).tolist() == [True, True]
    assert simulation.calculate("is_uc_claimant", YEAR).tolist() == [True, False]
    assert simulation.calculate("is_uc_assessed_claimant", YEAR).tolist() == [
        True,
        False,
    ]
    assert simulation.calculate("claims_universal_credit", YEAR)[0]
    assert amount(simulation, "universal_credit_pre_benefit_cap") > 0
    assert not simulation.calculate("is_uc_benefit_cap_exempt_specified_benefit", YEAR)[
        0
    ]
    cap = amount(simulation, "uc_benefit_cap")
    reduction = amount(simulation, "uc_benefit_cap_reduction_after_floor")
    final_uc = amount(simulation, "universal_credit")
    assert math.isfinite(cap) and cap > 0
    assert math.isfinite(reduction) and reduction >= 0
    assert math.isfinite(final_uc) and final_uc >= 0


def test_hb_specified_benefit_reader_honours_report_callback_contract(monkeypatch):
    """HB supplies the report callback needed beyond the same-couple fast path.

    Route the real HB reader through award_of_members to exercise its dormant
    callback contract. This does not invent another legal HB claimant mask.
    """
    import math

    import numpy as np

    from policyengine_uk.utils.benefit_unit import award_of_members

    people, benunits, households = {}, {}, {}
    for unit, report in (("paid_couple", 400), ("nil_couple", 200)):
        members = [f"{unit}_claimant", f"{unit}_outside"]
        for name, claimant in zip(members, (True, False)):
            inputs = {
                "age": 40 if claimant else 30,
                "is_claimant_or_partner": claimant,
                "employment_income": 0,
                "hours_worked": 0,
                "current_education": "NOT_IN_EDUCATION",
                "esa_income_reported": report if claimant else 3_000,
                "esa_contrib_reported": 0,
                "esa_includes_support_component": True,
                "care_hours": 0,
                "is_disabled_for_benefits": False,
                "person_legacy_benefits_closed": False,
            }
            people[name] = {key: {YEAR: value} for key, value in inputs.items()}
        benunits[unit] = {
            "members": members,
            "would_claim_uc": {YEAR: False},
            "would_claim_pc": {YEAR: False},
            "esa_income_assessable_capital": {YEAR: 7_000},
            "universal_credit_pre_benefit_cap": {YEAR: 0},
            "housing_benefit_pre_benefit_cap": {YEAR: 25_000},
            "working_tax_credit": {YEAR: 0},
        }
        households[unit] = {
            "members": members,
            "region": {YEAR: "NORTH_EAST"},
        }
    simulation = Simulation(
        situation={"people": people, "benunits": benunits, "households": households}
    )
    # The existing shared-capital proxy gives four £250 steps above £6,000:
    # £4 a week, £208 a year. The couple keeps 400 - 208 = 192 or nil;
    # each outside claimant keeps 3,000 - 208 = 2,792 on their separate claim.
    np.testing.assert_array_equal(
        simulation.calculate("is_claimant_or_partner", YEAR),
        [True, False, True, False],
    )
    np.testing.assert_array_equal(
        simulation.calculate("esa_income_report_closed", YEAR), [False] * 4
    )
    np.testing.assert_allclose(
        simulation.calculate("esa_income_tariff_income", YEAR),
        [208, 208],
        rtol=0,
        atol=0.01,
    )
    np.testing.assert_allclose(
        simulation.calculate("claimant_or_partner_esa_income", YEAR),
        [192, 0],
        rtol=0,
        atol=0.01,
    )
    np.testing.assert_allclose(
        simulation.calculate("esa_income", YEAR),
        [2_984, 2_792],
        rtol=0,
        atol=0.01,
    )

    scoped_awards = []

    def read_report_contract(benunit, period, award, report, award_on_reports, couple):
        scoped = award_of_members(
            benunit, period, award, report, award_on_reports, couple
        )
        scoped_awards.append(scoped.copy())
        return scoped

    specified = "is_housing_benefit_benefit_cap_exempt_specified_benefit"
    reader = simulation.tax_benefit_system.get_variable(specified).get_formula(YEAR)
    monkeypatch.setitem(reader.__globals__, "award_of_couple", read_report_contract)
    np.testing.assert_array_equal(simulation.calculate(specified, YEAR), [True, False])
    np.testing.assert_allclose(scoped_awards[0], [192, 0], rtol=0, atol=0.01)
    caps = simulation.calculate("housing_benefit_benefit_cap", YEAR)
    assert math.isinf(caps[0]) and math.isfinite(caps[1]) and caps[1] > 0
    reductions = simulation.calculate("housing_benefit_benefit_cap_reduction", YEAR)
    assert reductions[0] == 0
    assert math.isfinite(reductions[1]) and reductions[1] > 0
