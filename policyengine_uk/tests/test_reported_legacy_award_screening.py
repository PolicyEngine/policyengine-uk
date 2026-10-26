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
