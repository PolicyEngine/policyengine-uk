"""Housing Benefit additional-rule regressions from the operative legislation.

Capital: SI 2006/213 Sch 6, SI 2006/214 Sch 6, SI 2026/681 and SR 2026/146.
Earnings: SI 2006/213 Sch 4, SI 2006/214 Sch 4, SPC Regs 2002 Sch VI.
Cases use small situations only: no external datasets or generated populations.
"""

import numpy as np
import pytest

from policyengine_uk import Simulation
from policyengine_uk.utils.housing_benefit_capital import year_after


def family_simulation(
    *, year=2026, people=None, family=None, household=None, reform=None
):
    people = people or {"claimant": {"age": 40, "is_claimant_or_partner": True}}
    defaults = {
        "housing_benefit_pension_age_regulations_apply": False,
        "housing_benefit_on_passporting_benefit": False,
        "in_receipt_of_guarantee_credit": False,
        "in_receipt_of_savings_credit_only": False,
        "would_claim_uc": False,
        "working_tax_credit": 0,
        "child_tax_credit": 0,
    }
    defaults.update(family or {})
    situation = {
        "people": {
            name: {key: {str(year): value} for key, value in values.items()}
            for name, values in people.items()
        },
        "benunits": {
            "family": {
                "members": list(people),
                **{key: {str(year): value} for key, value in defaults.items()},
            }
        },
        "households": {
            "household": {
                "members": list(people),
                **{key: {str(year): value} for key, value in (household or {}).items()},
            }
        },
    }
    return Simulation(situation=situation, reform=reform)


@pytest.mark.parametrize(
    "date,provenance,expected",
    [
        ("2026-07-15", True, 12_000),
        ("2026-07-16", True, 2_000),
        ("2026-10-06", False, 12_000),
    ],
)
@pytest.mark.parametrize("country", ["ENGLAND", "NORTHERN_IRELAND"])
def test_carer_reassessment_commencement_and_provenance(
    date, provenance, expected, country
):
    simulation = family_simulation(
        people={
            "claimant": {
                "age": 40,
                "is_claimant_or_partner": True,
                "housing_benefit_capital_carer_reassessment_retained": 10_000,
                "housing_benefit_capital_carer_reassessment_received": "2026-07-01",
                "housing_benefit_capital_carer_reassessment_provenance": provenance,
            }
        },
        family={"housing_benefit_assessment_date": date},
        household={"savings": 12_000, "country": country},
    )
    assert (
        simulation.calculate("housing_benefit_assessable_capital", 2026)[0] == expected
    )


@pytest.mark.parametrize(
    "known,owned,expected", [(False, 0, 12_000), (True, 0, 0), (True, 3_000, 3_000)]
)
def test_known_capital_including_zero_replaces_proxy(known, owned, expected):
    simulation = family_simulation(
        family={
            "housing_benefit_owned_household_capital_known": known,
            "housing_benefit_owned_household_capital": owned,
        },
        household={"savings": 12_000},
    )
    assert (
        simulation.calculate("housing_benefit_assessable_capital", 2026)[0] == expected
    )


@pytest.mark.parametrize(
    "pension,first,received,expected",
    [
        (False, True, "2025-10-08", 2_000),
        (False, True, "2025-10-06", 12_000),
        (False, False, "2026-01-01", 12_000),
        (True, False, "2020-01-01", 2_000),
    ],
)
def test_personal_injury_direct_payment_rules(pension, first, received, expected):
    simulation = family_simulation(
        people={
            "claimant": {
                "age": 70 if pension else 40,
                "is_claimant_or_partner": True,
                "housing_benefit_capital_injury_payment_retained": 10_000,
                "housing_benefit_capital_injury_first_payment_received": received,
                "housing_benefit_capital_injury_payment_is_first": first,
            }
        },
        family={"housing_benefit_pension_age_regulations_apply": pension},
        household={"savings": 12_000},
    )
    assert (
        simulation.calculate("housing_benefit_assessable_capital", 2026)[0] == expected
    )


def test_pension_calendar_year_is_not_52_weeks():
    dates = np.array(["2023-03-01", "2024-02-29", "2024-10-06"], dtype="datetime64[D]")
    assert list(year_after(dates).astype(str)) == [
        "2024-03-01",
        "2025-02-28",
        "2025-10-06",
    ]


@pytest.mark.parametrize(
    "payment,official,award_start,expected",
    [
        (5_000, True, "2024-01-01", 7_000),
        (4_999, True, "2024-01-01", 12_000),
        (5_000, False, "2024-01-01", 12_000),
        (5_000, True, "2026-01-01", 12_000),
    ],
)
def test_large_error_arrears_require_threshold_and_continuing_award(
    payment, official, award_start, expected
):
    simulation = family_simulation(
        people={
            "claimant": {
                "age": 40,
                "is_claimant_or_partner": True,
                "housing_benefit_capital_qualifying_arrears_retained": 5_000,
                "housing_benefit_capital_arrears_total_payment": payment,
                "housing_benefit_capital_arrears_received": "2024-05-01",
                "housing_benefit_capital_arrears_official_error": official,
            }
        },
        family={"housing_benefit_continuous_award_start": award_start},
        household={"savings": 12_000},
    )
    assert (
        simulation.calculate("housing_benefit_assessable_capital", 2026)[0] == expected
    )


@pytest.mark.parametrize(
    "supervised,hours,weekly_earnings,approved,limit",
    [
        (False, 15.99, 203.50, True, 203.50),
        (False, 16, 203.50, True, 0),
        (True, 16, 203.50, True, 203.50),
        (True, 10, 203.51, True, 0),
        (False, 20, 20, True, 20),
        (False, 10, 100, False, 0),
    ],
)
def test_permitted_work_limits_and_factual_conditions(
    supervised, hours, weekly_earnings, approved, limit
):
    simulation = family_simulation(
        people={
            "claimant": {
                "age": 40,
                "is_claimant_or_partner": True,
                "esa_contrib": 1_000,
                "permitted_work_authority_approved": approved,
                "permitted_work_net_earnings": weekly_earnings,
                "permitted_work_weekly_hours": hours,
                "permitted_work_supported": supervised,
            }
        }
    )
    assert simulation.calculate("housing_benefit_permitted_work_limit", 2026)[
        0
    ] == pytest.approx(limit)


def test_permitted_work_couple_shares_one_limit_and_caps_other_ordinary_earnings():
    simulation = family_simulation(
        people={
            "claimant": {
                "age": 40,
                "is_claimant_or_partner": True,
                "housing_benefit_person_net_earnings": 90 * 52,
                "esa_contrib": 1_000,
                "permitted_work_authority_approved": True,
                "permitted_work_net_earnings": 90,
                "permitted_work_weekly_hours": 10,
            },
            "partner": {
                "age": 40,
                "is_claimant_or_partner": True,
                "housing_benefit_person_net_earnings": 100 * 52,
            },
        }
    )
    assert (
        simulation.calculate("housing_benefit_standard_earnings_disregard", 2026)[0]
        == 110 * 52
    )


def test_working_age_carer_with_low_earnings_does_not_get_flat_twenty():
    simulation = family_simulation(
        people={
            "claimant": {
                "age": 40,
                "is_claimant_or_partner": True,
                "housing_benefit_person_net_earnings": 4 * 52,
                "is_entitled_to_carer_benefit": True,
            },
            "partner": {
                "age": 40,
                "is_claimant_or_partner": True,
                "housing_benefit_person_net_earnings": 40 * 52,
            },
        }
    )
    assert (
        simulation.calculate("housing_benefit_standard_earnings_disregard", 2026)[0]
        == 14 * 52
    )


@pytest.mark.parametrize(
    "evidence,date,expected",
    [
        (False, "2026-01-01", 7_500),
        (True, "2026-10-07", 7_500),
        (True, "2026-10-06", 10_000),
    ],
)
def test_lisa_requires_provider_held_qualifying_evidence_received(
    evidence, date, expected
):
    simulation = family_simulation(
        people={
            "claimant": {
                "age": 40,
                "is_claimant_or_partner": True,
                "lifetime_isa_balance": 10_000,
                "lifetime_isa_qualifying_medical_evidence": evidence,
                "lifetime_isa_medical_evidence_received_date": date,
            }
        }
    )
    assert simulation.calculate("lifetime_isa_countable_capital", 2026)[0] == expected


def children(number, **facts):
    return {
        "claimant": {"age": 40, "is_claimant_or_partner": True},
        **{
            f"child_{index}": {
                "age": 5 + index,
                "is_claimant_or_partner": False,
                "is_child_or_young_person_for_legacy_benefits": True,
                **facts,
            }
            for index in range(number)
        },
    }


@pytest.mark.parametrize(
    "year,pension,country,count,expected_children",
    [
        (2016, False, "ENGLAND", 3, 3),
        (2020, False, "ENGLAND", 3, 2),
        (2020, True, "NORTHERN_IRELAND", 3, 2),
        (2025, True, "ENGLAND", 3, 3),
        (2025, False, "NORTHERN_IRELAND", 3, 2),
        (2026, False, "ENGLAND", 3, 3),
    ],
)
def test_child_allowance_history_and_two_child_limit(
    year, pension, country, count, expected_children
):
    simulation = family_simulation(
        year=year,
        people=children(count),
        family={"housing_benefit_pension_age_regulations_apply": pension},
        household={"country": country},
    )
    rate = simulation.tax_benefit_system.parameters(
        str(year)
    ).gov.dwp.housing_benefit.allowances.child
    assert simulation.calculate("housing_benefit_child_allowance", year)[
        0
    ] == pytest.approx(expected_children * rate * 52, abs=0.01)


@pytest.mark.parametrize(
    "new_claim,ctc_elements,continuing_children,expected_children",
    [
        (False, 0, 3, 3),
        (True, 0, 3, 2),
        (False, 0, 2, 2),
        (False, 4, 2, 4),
        (True, 3, 0, 3),
    ],
)
def test_only_continuing_children_or_actual_ctc_award_protect_larger_families(
    new_claim, ctc_elements, continuing_children, expected_children
):
    people = children(4)
    for index in range(continuing_children):
        people[f"child_{index}"][
            "housing_benefit_child_in_family_at_two_child_limit_start"
        ] = True
    simulation = family_simulation(
        year=2020,
        people=people,
        family={
            "housing_benefit_entitled_at_two_child_limit_start": True,
            "housing_benefit_child_count_at_two_child_limit_start": 3,
            "housing_benefit_new_claim_since_two_child_limit_start": new_claim,
            "housing_benefit_ctc_child_element_count": ctc_elements,
            "child_tax_credit": 0,
        },
    )
    assert simulation.calculate("housing_benefit_child_allowance", 2020)[
        0
    ] == pytest.approx(expected_children * 68.27 * 52, abs=0.01)


@pytest.mark.parametrize(
    "pension,age,expected",
    [
        (True, 64, (163 * 244 / 365 + 176.4 * 121 / 365) * 52),
        (True, 65, 176.4 * 52),
        (False, 64, 73.1 * 52),
    ],
)
def test_2018_under_65_category_ends_within_the_fiscal_year(pension, age, expected):
    simulation = family_simulation(
        year=2018,
        people={"claimant": {"age": age, "is_claimant_or_partner": True}},
        family={
            "housing_benefit_eligible": True,
            "housing_benefit_pension_age_regulations_apply": pension,
            "benefits_premiums": 0,
        },
    )
    assert simulation.calculate("housing_benefit_applicable_amount", 2018)[
        0
    ] == pytest.approx(expected, abs=0.02)


@pytest.mark.parametrize(
    "protected,continuing,new_claim,pension,old_lone,weekly",
    [
        (False, False, False, False, False, 0),
        (True, True, False, False, False, 20.22),
        (True, False, False, False, False, 0),
        (True, True, True, False, False, 0),
        (True, True, False, False, True, 22.2),
        (True, True, False, True, True, 20.22),
    ],
)
def test_family_premium_requires_actual_abolition_and_lone_parent_protection(
    protected, continuing, new_claim, pension, old_lone, weekly
):
    simulation = family_simulation(
        people=children(1),
        family={
            "housing_benefit_family_premium_entitled_before_abolition": protected,
            "housing_benefit_family_premium_family_condition_continued": continuing,
            "housing_benefit_family_premium_new_claim_since_abolition": new_claim,
            "housing_benefit_lone_parent_family_premium_1998_protection": old_lone,
            "housing_benefit_pension_age_regulations_apply": pension,
        },
    )
    assert simulation.calculate("housing_benefit_family_premium", 2026)[
        0
    ] == pytest.approx(weekly * 52, abs=0.01)


@pytest.mark.parametrize("pension", [False, True])
@pytest.mark.parametrize(
    "child_facts,weekly",
    [
        ({"is_disabled_for_benefits": True, "dla": 0, "pip": 0}, 0),
        ({"dla": 100, "dla_sc_category": "MIDDLE"}, 84.46),
        ({"dla": 100, "dla_sc_category": "HIGHER"}, 84.46 + 33.99),
        (
            {"housing_benefit_child_enhanced_disability_payment_or_suspension": True},
            84.46 + 33.99,
        ),
        ({"is_blind": True}, 84.46),
        (
            {
                "is_child_or_young_person_for_legacy_benefits": False,
                "housing_benefit_child_benefit_after_death": True,
                "housing_benefit_disabled_child_premium_before_death": True,
            },
            84.46,
        ),
    ],
)
def test_child_premiums_are_separate_and_require_statutory_award_facts(
    pension, child_facts, weekly
):
    simulation = family_simulation(
        people=children(1, **child_facts),
        family={"housing_benefit_pension_age_regulations_apply": pension},
    )
    assert simulation.calculate("housing_benefit_child_disability_premiums", 2026)[
        0
    ] == pytest.approx(weekly * 52, abs=0.01)


@pytest.mark.parametrize(
    "childcare,expected_weekly", [(70, 20), (62.9, 37.1), (60, 37.1)]
)
def test_additional_earnings_disregard_coverage_includes_childcare(
    childcare, expected_weekly
):
    simulation = family_simulation(
        people={
            "claimant": {
                "age": 40,
                "is_claimant_or_partner": True,
                "housing_benefit_person_net_earnings": 100 * 52,
            }
        },
        family={
            "disability_premium": 100,
            "housing_benefit_applicable_income_childcare_element": childcare * 52,
            "meets_housing_benefit_additional_earnings_disregard_conditions": True,
        },
    )
    assert simulation.calculate("housing_benefit_applicable_income_disregard", 2026)[
        0
    ] == pytest.approx(expected_weekly * 52, abs=0.01)


def test_savings_credit_only_retains_pc_disregard_and_does_not_deduct_it_twice():
    simulation = family_simulation(
        people={
            "claimant": {
                "age": 80,
                "is_claimant_or_partner": True,
                "housing_benefit_person_net_earnings": 100 * 52,
            }
        },
        family={
            "housing_benefit_pension_age_regulations_apply": True,
            "in_receipt_of_savings_credit_only": True,
            "housing_benefit_pension_credit_net_income_assessment": 10_000,
            "pension_credit": 500,
            "housing_benefit_pension_credit_earnings_disregard_assessment": 5 * 52,
            "housing_benefit_standard_earnings_disregard": 20 * 52,
            "housing_benefit_applicable_income_childcare_element": 0,
            "meets_housing_benefit_additional_earnings_disregard_conditions": False,
        },
    )
    assert (
        simulation.calculate("housing_benefit_applicable_income_disregard", 2026)[0]
        == 5 * 52
    )
    assert (
        simulation.calculate("housing_benefit_savings_credit_only_income", 2026)[0]
        == 10_500
    )


def test_housing_benefit_reform_does_not_change_reported_pc_assessment():
    people = {
        "claimant": {
            "age": 70,
            "is_claimant_or_partner": True,
            "employment_income": 10,
            "self_employment_income": 0,
            "employment_benefits": 0,
            "total_income": 10,
            "income_tax": 0,
            "ni_class_1_employee": 0,
            "ni_class_2": 0,
            "ni_class_4": 0,
            "pension_contributions": 10,
        }
    }
    assessment = {
        "housing_benefit_pension_credit_earnings_disregard_assessment": 5,
        "housing_benefit_pension_credit_net_income_assessment": 100,
    }
    baseline = family_simulation(people=people, family=assessment)
    reformed = family_simulation(
        people=people,
        family=assessment,
        reform={
            "gov.dwp.housing_benefit.means_test.pension_contribution_deduction_rate": {
                "2026": 0
            }
        },
    )
    assert baseline.calculate("housing_benefit_person_net_earnings", 2026)[0] == 5
    assert reformed.calculate("housing_benefit_person_net_earnings", 2026)[0] == 10
    for simulation in (baseline, reformed):
        assert (
            simulation.calculate(
                "housing_benefit_pension_credit_earnings_disregard_assessment", 2026
            )[0]
            == 5
        )
        assert (
            simulation.calculate(
                "housing_benefit_pension_credit_net_income_assessment", 2026
            )[0]
            == 100
        )


@pytest.mark.parametrize(
    "pension,received,extension,expected",
    [
        (False, "2026-04-08", "9999-01-01", 2_000),
        (False, "2026-04-07", "9999-01-01", 12_000),
        (False, "2026-01-01", "2026-10-06", 2_000),
        (True, "2025-10-07", "9999-01-01", 2_000),
        (True, "2025-10-06", "2027-01-01", 12_000),
    ],
)
def test_home_funds_have_regime_specific_durations(
    pension, received, extension, expected
):
    simulation = family_simulation(
        people={
            "claimant": {
                "age": 70 if pension else 40,
                "is_claimant_or_partner": True,
                "housing_benefit_capital_home_funds_retained": 10_000,
                "housing_benefit_capital_home_funds_received": received,
                "housing_benefit_capital_home_funds_extension_end": extension,
            }
        },
        family={"housing_benefit_pension_age_regulations_apply": pension},
        household={"savings": 12_000},
    )
    assert (
        simulation.calculate("housing_benefit_assessable_capital", 2026)[0] == expected
    )


@pytest.mark.parametrize(
    "facts,expected",
    [
        ({"housing_benefit_capital_business_active": True}, 2_000),
        (
            {
                "housing_benefit_capital_business_ceased": "2025-01-01",
                "housing_benefit_capital_business_disposal_steps": True,
                "housing_benefit_capital_business_extension_end": "2026-10-06",
            },
            2_000,
        ),
        (
            {
                "housing_benefit_capital_business_ceased": "2025-01-01",
                "housing_benefit_capital_business_disposal_steps": False,
                "housing_benefit_capital_business_extension_end": "2026-10-06",
            },
            12_000,
        ),
        ({"housing_benefit_capital_business_illness_and_return": True}, 2_000),
    ],
)
def test_business_assets_require_active_business_disposal_or_illness_conditions(
    facts, expected
):
    simulation = family_simulation(
        people={
            "claimant": {
                "age": 40,
                "is_claimant_or_partner": True,
                "housing_benefit_capital_business_assets": 10_000,
                **facts,
            }
        },
        family={"housing_benefit_continuous_award_start": "2026-05-01"},
        household={"corporate_wealth": 12_000},
    )
    assert (
        simulation.calculate("housing_benefit_assessable_capital", 2026)[0] == expected
    )


@pytest.mark.parametrize(
    "category,intended,steps,expected",
    [
        ("ACQUIRED_HOME", True, False, 2_000),
        ("ACQUIRED_HOME", False, False, 12_000),
        ("SALE", False, True, 2_000),
        ("SALE", False, False, 12_000),
        ("LEGAL_POSSESSION", True, True, 2_000),
        ("ESSENTIAL_REPAIRS", False, True, 12_000),
    ],
)
def test_temporary_premises_categories_require_their_own_purpose_and_steps(
    category, intended, steps, expected
):
    simulation = family_simulation(
        people={
            "claimant": {
                "age": 40,
                "is_claimant_or_partner": True,
                "housing_benefit_capital_temporary_premises": 10_000,
                "housing_benefit_capital_premises_category": category,
                "housing_benefit_capital_premises_intended_home": intended,
                "housing_benefit_capital_premises_reasonable_steps": steps,
                "housing_benefit_capital_premises_first_step": "2026-05-01",
            }
        },
        household={"other_residential_property_value": 12_000},
    )
    assert (
        simulation.calculate("housing_benefit_assessable_capital", 2026)[0] == expected
    )


@pytest.mark.parametrize(
    "relative,old,incapacitated,expected",
    [
        (True, True, False, 2_000),
        (True, False, True, 2_000),
        (True, False, False, 12_000),
        (False, True, True, 12_000),
    ],
)
def test_relative_occupied_premises_not_every_second_home(
    relative, old, incapacitated, expected
):
    simulation = family_simulation(
        people={
            "claimant": {
                "age": 40,
                "is_claimant_or_partner": True,
                "housing_benefit_capital_relative_occupied_premises": 10_000,
                "housing_benefit_capital_property_occupier_is_relative": relative,
                "housing_benefit_capital_property_occupier_over_qualifying_age": old,
                "housing_benefit_capital_property_occupier_incapacitated": incapacitated,
            }
        },
        household={"other_residential_property_value": 12_000},
    )
    assert (
        simulation.calculate("housing_benefit_assessable_capital", 2026)[0] == expected
    )


def test_excluded_personal_capital_is_removed_before_proxy_allocation():
    situation = {
        "people": {
            "first": {
                "age": {2026: 40},
                "is_claimant_or_partner": {2026: True},
                "housing_benefit_capital_injury_trust": {2026: 10_000},
            },
            "second": {"age": {2026: 40}, "is_claimant_or_partner": {2026: True}},
        },
        "benunits": {
            name: {
                "members": [person],
                "housing_benefit_pension_age_regulations_apply": {2026: False},
                "housing_benefit_on_passporting_benefit": {2026: False},
                "in_receipt_of_guarantee_credit": {2026: False},
            }
            for name, person in [("first_family", "first"), ("second_family", "second")]
        },
        "households": {
            "home": {"members": ["first", "second"], "savings": {2026: 12_000}}
        },
    }
    simulation = Simulation(situation=situation)
    np.testing.assert_allclose(
        simulation.calculate("housing_benefit_assessable_capital", 2026), [1_000, 1_000]
    )
    situation["benunits"]["second_family"].update(
        {
            "housing_benefit_owned_household_capital_known": {2026: True},
            "housing_benefit_owned_household_capital": {2026: 4_000},
        }
    )
    owned = Simulation(situation=situation)
    np.testing.assert_allclose(
        owned.calculate("housing_benefit_assessable_capital", 2026), [1_000, 4_000]
    )


@pytest.mark.parametrize(
    "sick_start,previous_work,expected",
    [
        ("2026-03-25", True, True),
        ("2026-03-24", True, False),
        ("2026-03-25", False, False),
    ],
)
def test_childcare_sickness_treatment_requires_preceding_work_and_first_28_weeks(
    sick_start, previous_work, expected
):
    simulation = family_simulation(
        people={
            "claimant": {
                "age": 40,
                "is_claimant_or_partner": True,
                "weekly_hours": 0,
                "housing_benefit_childcare_work_before_absence": previous_work,
                "housing_benefit_childcare_sickness_start": sick_start,
                "statutory_sick_pay": 1_000,
            }
        }
    )
    assert (
        bool(simulation.calculate("housing_benefit_childcare_treated_as_work", 2026)[0])
        is expected
    )


@pytest.mark.parametrize(
    "partner_facts,expected",
    [
        ({"weekly_hours": 16, "employment_income": 1_000}, True),
        ({"weekly_hours": 0, "is_hospital_inpatient": True}, True),
        ({"weekly_hours": 0, "is_in_prison": True}, True),
        (
            {"weekly_hours": 0, "is_disabled_for_benefits": True, "dla": 0, "pip": 0},
            False,
        ),
        ({"weekly_hours": 0, "dla": 1_000}, True),
    ],
)
def test_couple_childcare_work_condition_requires_partner_work_or_listed_incapacity(
    partner_facts, expected
):
    simulation = family_simulation(
        people={
            "claimant": {
                "age": 40,
                "is_claimant_or_partner": True,
                "weekly_hours": 16,
                "employment_income": 1_000,
            },
            "partner": {"age": 40, "is_claimant_or_partner": True, **partner_facts},
        },
        family={"disability_premium": 0},
    )
    assert (
        bool(simulation.calculate("housing_benefit_childcare_work_condition", 2026)[0])
        is expected
    )


def test_claimant_wr_ag_status_alone_establishes_esa_age_exception():
    simulation = family_simulation(
        people={
            "claimant": {
                "age": 22,
                "is_claimant_or_partner": True,
                "is_housing_benefit_claimant": True,
                "esa_work_related_activity_group": True,
                "esa_claim_made": False,
                "esa_assessment_phase_ended": False,
            }
        },
        family={"housing_benefit_eligible": True, "benefits_premiums": 0},
    )
    assert simulation.calculate("housing_benefit_applicable_amount", 2026)[
        0
    ] == pytest.approx(95.55 * 52, abs=0.01)


@pytest.mark.parametrize(
    "country,open_days", [("ENGLAND", 25), ("NORTHERN_IRELAND", 152)]
)
def test_family_premium_abolition_uses_the_jurisdiction_specific_fiscal_year_date(
    country, open_days
):
    simulation = family_simulation(
        year=2016, people=children(1), household={"country": country}
    )
    assert simulation.calculate("housing_benefit_family_premium", 2016)[
        0
    ] == pytest.approx(17.45 * 52 * open_days / 365, abs=0.01)


def test_disabled_child_premiums_are_not_limited_to_two_child_personal_allowances():
    simulation = family_simulation(
        year=2020, people=children(3, dla=1_000, dla_sc_category="HIGHER")
    )
    assert simulation.calculate("housing_benefit_child_allowance", 2020)[
        0
    ] == pytest.approx(2 * 68.27 * 52, abs=0.01)
    assert simulation.calculate("housing_benefit_child_disability_premiums", 2020)[
        0
    ] == pytest.approx(3 * (65.52 + 26.60) * 52, abs=0.01)


def test_explicit_child_allowance_reform_remains_authoritative():
    simulation = family_simulation(
        people=children(3),
        reform={
            "gov.dwp.housing_benefit.allowances.child": {"2026": 100},
        },
    )
    assert (
        simulation.calculate("housing_benefit_child_allowance", 2026)[0] == 3 * 100 * 52
    )


@pytest.mark.parametrize(
    "facts,expected",
    [
        ({"incapacity_benefit": 1_000}, False),
        (
            {
                "incapacity_benefit": 1_000,
                "incapacity_benefit_is_short_term_lower_rate": True,
            },
            False,
        ),
        (
            {
                "incapacity_benefit": 1_000,
                "incapacity_benefit_is_short_term_higher_rate": True,
            },
            True,
        ),
        ({"housing_benefit_childcare_listed_incapacity_benefit_payable": True}, True),
        ({"housing_benefit_childcare_incapacity_but_for_determination": True}, True),
    ],
)
def test_childcare_incapatity_requires_positive_rate_or_statutory_condition(
    facts, expected
):
    simulation = family_simulation(
        people={"claimant": {"age": 40, "is_claimant_or_partner": True, **facts}},
        family={"disability_premium": 0},
    )
    assert (
        bool(simulation.calculate("housing_benefit_childcare_incapacitated", 2026)[0])
        is expected
    )


def test_pc_assessment_adapter_uses_the_separately_installed_pc_component():
    from policyengine_core.reforms import Reform
    from policyengine_uk.model_api import BenUnit, Variable, YEAR

    class pension_credit_earnings_disregard(Variable):
        value_type = float
        entity = BenUnit
        definition_period = YEAR
        label = "Test Pension Credit earnings disregard"

        def formula(benunit, period, parameters):
            return np.full(benunit.count, 260.0)

    class WithPensionCreditComponent(Reform):
        def apply(self):
            self.add_variable(pension_credit_earnings_disregard)

    without = family_simulation()
    with_component = family_simulation(reform=WithPensionCreditComponent)
    name = "housing_benefit_pension_credit_earnings_disregard_assessment"
    assert without.calculate(name, 2026)[0] == 0
    assert with_component.calculate(name, 2026)[0] == 260
