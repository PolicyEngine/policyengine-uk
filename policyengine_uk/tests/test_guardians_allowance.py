"""Guardian's Allowance's explicit cash, legal-holder and integration contract.

SSCBA 1992 s77 entitlement is a supplied fact, distinct from the payment's
recipient. UC Reg83 and HB Reg75F exempt the people each provision names even
when cash is nil. ITEPA s677 exempts the payment from tax; the means-test
regulations disregard it. These tests do not adjudicate orphan/claim facts.
"""

from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest
import yaml

from policyengine_uk import CountryTaxBenefitSystem, Simulation

YEAR = 2026
MODEL = Path(__file__).parents[1]
UC_SPECIFIED = "is_uc_benefit_cap_exempt_specified_benefit"
HB_SPECIFIED = "is_housing_benefit_benefit_cap_exempt_specified_benefit"
TOTALS = (
    "household_benefits",
    "hbai_benefits",
    "hbai_household_net_income",
    "household_net_income",
    "gov_spending",
)


def family(people, *, year=YEAR, benunit=None, household=None):
    """A public situation with explicitly supplied family roles and no dataset."""
    names = [f"person{i + 1}" for i in range(len(people))]
    return {
        "people": {
            name: {key: {year: value} for key, value in person.items()}
            for name, person in zip(names, people)
        },
        "benunits": {
            "family": {"members": names, **(benunit or {})},
        },
        "households": {
            "home": {
                "members": names,
                "country": "ENGLAND",
                "tenure_type": "OWNED_OUTRIGHT",
                **(household or {}),
            }
        },
    }


def guardian(**extra):
    return {
        "age": 40,
        "is_claimant_or_partner": True,
        "is_entitled_to_guardians_allowance": True,
        "guardians_allowance": 0,
        **extra,
    }


def child(**extra):
    return {
        "age": 8,
        "is_claimant_or_partner": False,
        "guardians_allowance": 0,
        **extra,
    }


def snapshot(situation, variables, year=YEAR):
    # Return copied values, not a live simulation, before the comparison world
    # is built. No forced garbage collection or changed calculation semantics.
    simulation = Simulation(situation=deepcopy(situation))
    return {
        variable: np.asarray(simulation.calculate(variable, year)).copy()
        for variable in variables
    }


def test_claimant_entitlement_with_nil_cash_lifts_both_caps():
    """UC83(1)(k), HB75F(1)(i): entitled, rather than receiving cash."""
    values = snapshot(
        family([guardian(), child()]),
        (UC_SPECIFIED, HB_SPECIFIED, "guardians_allowance"),
    )
    assert values[UC_SPECIFIED].tolist() == [True]
    assert values[HB_SPECIFIED].tolist() == [True]
    assert values["guardians_allowance"].tolist() == [0, 0]


@pytest.mark.parametrize(
    "role,expected_uc,expected_hb",
    [
        ("joint_partner", True, True),
        ("excluded_single_claim_partner", False, True),
        ("responsible_qualifying_young_person", False, True),
        ("non_qualifying_member", False, False),
    ],
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_cap_entitlement_is_limited_to_each_schemes_legal_holders(
    role, expected_uc, expected_hb
):
    first = guardian(is_entitled_to_guardians_allowance=False)
    if role in ("joint_partner", "excluded_single_claim_partner"):
        holder = guardian(age=38)
        if role == "excluded_single_claim_partner":
            holder["uc_is_ineligible_partner"] = True
        people = [first, holder, child()]
    else:
        # An independently qualified 17-year-old holder, not the household's
        # claimant/partner. HB alone includes a responsible qualifying young
        # person; an explicitly non-qualifying member cannot lift either cap.
        holder = child(
            age=17,
            is_entitled_to_guardians_allowance=True,
            current_education=(
                "UPPER_SECONDARY"
                if role == "responsible_qualifying_young_person"
                else "NOT_IN_EDUCATION"
            ),
        )
        people = [first, holder]
    names = (
        UC_SPECIFIED,
        HB_SPECIFIED,
        "is_uc_single_or_joint_claimant",
        "is_qualifying_young_person_for_child_benefit",
        "guardians_allowance",
    )
    values = snapshot(family(people), names)
    assert values[UC_SPECIFIED].tolist() == [expected_uc]
    assert values[HB_SPECIFIED].tolist() == [expected_hb]
    if role == "excluded_single_claim_partner":
        assert values["is_uc_single_or_joint_claimant"].tolist() == [True, False, False]
    if "member" in role or "young_person" in role:
        assert bool(values["is_qualifying_young_person_for_child_benefit"][1]) == (
            role == "responsible_qualifying_young_person"
        )
    assert not values["guardians_allowance"].any()


def test_lawful_spouse_payee_does_not_transfer_entitlement_or_exempt_other_units():
    # s77(9) permits payment to a spouse/civil partner residing with the holder.
    # Both are in the SAME couple benefit unit; the other family shares only
    # their household. Every cash cell, including the holder's nil, is reported.
    situation = family(
        [
            guardian(),
            guardian(
                age=38,
                is_entitled_to_guardians_allowance=False,
                guardians_allowance=500,
            ),
            child(),
            guardian(age=45, is_entitled_to_guardians_allowance=False),
            child(age=6),
        ]
    )
    situation["benunits"] = {
        "first": {"members": ["person1", "person2", "person3"]},
        "second": {"members": ["person4", "person5"]},
    }
    values = snapshot(
        situation,
        (
            UC_SPECIFIED,
            HB_SPECIFIED,
            "guardians_allowance",
            "is_entitled_to_guardians_allowance",
        ),
    )
    assert values[UC_SPECIFIED].tolist() == [True, False]
    assert values[HB_SPECIFIED].tolist() == [True, False]
    assert values["guardians_allowance"].tolist() == [0, 500, 0, 0, 0]
    assert values["is_entitled_to_guardians_allowance"].tolist() == [
        True,
        False,
        False,
        False,
        False,
    ]


def test_ga_counted_once_in_totals():
    """A separate, tax-free £500 payment adds £500 to each cash total."""

    def amounts(payment):
        return snapshot(
            family(
                [
                    guardian(
                        age=70,
                        private_pension_income=40_000,
                        miscellaneous_income=137,
                        guardians_allowance=payment,
                    ),
                    child(),
                ],
                benunit={"would_claim_uc": False},
            ),
            (*TOTALS, "miscellaneous_income", "pension_credit", "universal_credit"),
        )

    before = amounts(0)
    assert not before["pension_credit"].any()
    assert not before["universal_credit"].any()
    after = amounts(500)
    for total in TOTALS:
        np.testing.assert_allclose(
            after[total] - before[total], [500], rtol=0, atol=0.01
        )
    # GA was separately supplied: no guessed offset against this unrelated £137.
    assert after["miscellaneous_income"].tolist() == [137, 0]


def test_cb_payment_opt_out_does_not_remove_ga_or_increase_tax_or_hicbc():
    """CB entitlement survives a high-income payment opt-out; GA is tax-free."""

    def amounts(reported_zero):
        first = guardian(
            employment_income=90_000, guardians_allowance_full_rate_child_weeks=52
        )
        second = child()
        if not reported_zero:
            del first["guardians_allowance"]
            del second["guardians_allowance"]
        return snapshot(
            family(
                [first, second],
                benunit={
                    "child_benefit_opts_out": {YEAR: True},
                    "would_claim_child_benefit": {YEAR: True},
                    "would_claim_uc": {YEAR: False},
                },
            ),
            (
                "guardians_allowance",
                "child_benefit_entitlement",
                "child_benefit",
                "CB_HITC",
                "income_tax",
                "adjusted_net_income",
                "taxable_social_security_income",
            ),
        )

    before = amounts(True)
    assert before["child_benefit_entitlement"][0] > 0
    assert before["income_tax"][0] > 0
    assert before["adjusted_net_income"][0] == pytest.approx(90_000)
    assert not before["child_benefit"].any()
    assert not before["CB_HITC"].any()
    after = amounts(False)
    assert after["guardians_allowance"].tolist() == pytest.approx(
        [1_193.40, 0], abs=0.01
    )
    for name in (
        "child_benefit_entitlement",
        "child_benefit",
        "CB_HITC",
        "income_tax",
        "adjusted_net_income",
        "taxable_social_security_income",
    ):
        np.testing.assert_allclose(after[name], before[name], rtol=0, atol=0.01)


@pytest.mark.parametrize(
    "benefit,income_read",
    [
        ("universal_credit", "uc_unearned_income"),
        ("housing_benefit", "housing_benefit_applicable_income"),
        ("pension_credit", "pension_credit_income"),
        ("income_support", "income_support_applicable_income"),
        ("jsa_income", "jsa_income_tariff_income"),
        ("esa_income", "esa_income_tariff_income"),
    ],
    ids=lambda value: value,
)
def test_ga_does_not_reduce_a_positive_uncapped_means_tested_award(
    benefit, income_read
):
    # 2025 keeps IS/JSA inside their actual active window (they end April2026).
    # JSA/ESA are reported-award screens in this model, not full entitlement
    # models; those positive reports still pass the real work/capital screen.
    def amounts(payment):
        first = guardian(guardians_allowance=payment)
        second = child(age=2)
        unit = {"would_claim_uc": benefit == "universal_credit"}
        home = {}
        if benefit == "pension_credit":
            first.update(age=70, state_pension=5_000)
        elif benefit == "income_support":
            first.update(income_support_reported=1_000, is_parent=True)
        elif benefit == "jsa_income":
            first["jsa_income_reported"] = 3_000
            home["savings"] = 6_500
        elif benefit == "esa_income":
            first["esa_income_reported"] = 3_000
            home["savings"] = 6_500
        elif benefit == "housing_benefit":
            first["housing_benefit_reported"] = 3_000
            home = {"tenure_type": "RENT_PRIVATELY", "rent": 6_000}
        values = (benefit, income_read)
        if benefit == "universal_credit":
            values += ("uc_benefit_cap_reduction",)
        elif benefit == "housing_benefit":
            values += ("housing_benefit_benefit_cap_reduction",)
        return snapshot(
            family([first, second], year=2025, benunit=unit, household=home),
            values,
            2025,
        )

    before = amounts(0)
    assert before[benefit][0] > 0, "An unchanged zero is not a disregard test"
    if benefit in ("jsa_income", "esa_income"):
        assert before[income_read][0] > 0
        assert before[benefit][0] < 3_000
    for name, value in before.items():
        if name.endswith("benefit_cap_reduction"):
            assert not value.any(), (
                "Test the income disregard separately from cap lifting"
            )
    after = amounts(500)
    assert after[benefit][0] > 0
    for name in before:
        np.testing.assert_allclose(after[name], before[name], rtol=0, atol=0.01)


def test_positive_computed_exposure_before_2024_requires_direct_cash():
    year = 2023
    situation = family(
        [guardian(guardians_allowance_full_rate_child_weeks=52), child()], year=year
    )
    for person in situation["people"].values():
        person.pop("guardians_allowance")
    simulation = Simulation(situation=situation)
    with pytest.raises(ValueError) as error:
        simulation.calculate("guardians_allowance", year)
    message = str(error.value).lower()
    assert "2024" in message and "direct" in message


@pytest.mark.parametrize("year", [2023, 2027])
@pytest.mark.parametrize("payment", [123.45, 0], ids=["positive", "zero"])
def test_direct_cash_remains_authoritative_with_positive_exposure(year, payment):
    values = snapshot(
        family(
            [
                guardian(
                    guardians_allowance_full_rate_child_weeks=52,
                    guardians_allowance=payment,
                ),
                child(),
            ],
            year=year,
        ),
        ("guardians_allowance",),
        year,
    )
    assert values["guardians_allowance"].tolist() == pytest.approx(
        [payment, 0], abs=0.01
    )


@pytest.mark.parametrize("year", [2023, 2027])
def test_no_payable_exposure_needs_no_unsupported_rate(year):
    situation = family([guardian(), child()], year=year)
    for person in situation["people"].values():
        person.pop("guardians_allowance")
    values = snapshot(situation, ("guardians_allowance",), year)
    assert values["guardians_allowance"].tolist() == [0, 0]


def test_enacted_dates_announced_rate_and_annual_labels():
    rates = yaml.safe_load(
        (MODEL / "parameters/gov/hmrc/guardians_allowance/weekly_rate.yaml").read_text()
    )
    raw = {
        str(date): value["value"] if isinstance(value, dict) else value
        for date, value in rates["values"].items()
    }
    assert raw == {
        "2024-04-08": 21.75,
        "2025-04-07": 22.10,
        "2026-04-06": 22.95,
        # Annual model reference date for the announced 2027–28 rate,
        # not a claimed statutory commencement date.
        "2027-04-30": 23.75,
    }
    assert rates["metadata"]["uprating"] == "gov.benefit_uprating_cpi"
    cap = yaml.safe_load((MODEL / "parameters/gov/dwp/benefit_cap.yaml").read_text())
    values = {
        str(date): value["value"] if isinstance(value, dict) else value
        for date, value in cap["guardians_allowance_exempt"]["values"].items()
    }
    assert type(values["0001-01-01"]) is bool
    assert type(values["2016-11-07"]) is bool
    assert values["0001-01-01"] is False
    assert values["2016-11-07"] is True
    assert any(date < "2016-11-07" and value is False for date, value in values.items())
    system = CountryTaxBenefitSystem()
    for year, amount in [
        (2024, 21.75),
        (2025, 22.10),
        (2026, 22.95),
        (2027, 23.75),
    ]:
        assert (
            system.parameters(str(year)).gov.hmrc.guardians_allowance.weekly_rate
            == amount
        )
    # Ordinary April30 annualisation: not the exact 2016 UC AP transition or
    # Northern Ireland's historical rollout.
    old = system.parameters("2016").gov.dwp.benefit_cap.guardians_allowance_exempt
    new = system.parameters("2017").gov.dwp.benefit_cap.guardians_allowance_exempt
    assert isinstance(old, (bool, np.bool_)) and isinstance(new, (bool, np.bool_))
    assert not old
    assert new


def test_partial_program_metadata_bounds_and_fiscal_head_survive_loading():
    registry = yaml.safe_load((MODEL / "programs.yaml").read_text())["programs"]
    entries = [p for p in registry if p["id"] == "guardians_allowance"]
    assert len(entries) == 1
    program = entries[0]
    for field, expected in {
        "status": "partial",
        "agency": "HMRC",
        "coverage": "UK",
        "verified_start_year": 2024,
        "verified_end_year": 2026,
        "variable": "guardians_allowance",
        "parameter_prefix": "gov.hmrc.guardians_allowance",
    }.items():
        assert program[field] == expected
    notes = program["notes"].lower()
    assert "entitlement" in notes and "payee" in notes
    assert "2026" in notes and "data" in notes
    system = CountryTaxBenefitSystem()
    loaded = next(
        p
        for p in system.modelled_policies["programs"]
        if p["id"] == "guardians_allowance"
    )
    for field, value in program.items():
        assert loaded[field] == value
    assert "guardians_allowance" in system.variables
    partition = yaml.safe_load((MODEL / "data/fiscal_partition.yaml").read_text())
    heads = [
        h for h in partition["spending_heads"] if h["variable"] == "guardians_allowance"
    ]
    assert len(heads) == 1
    assert heads[0]["report_group"] == "child_and_family_benefits"
    assert heads[0]["entity"] == "person"
    assert set(heads[0]["totals"]) == {"gov_spending", "household_benefits"}


@pytest.mark.parametrize("year,expected", [(2016, False), (2017, True)])
def test_annual_gb_cap_exemption_does_not_backdate_before_commencement(year, expected):
    # Annual April30 labels only: not UC assessment-period transitions or NI rollout.
    values = snapshot(
        family([guardian(), child()], year=year),
        (UC_SPECIFIED, HB_SPECIFIED),
        year,
    )
    assert values[UC_SPECIFIED].tolist() == [expected]
    assert values[HB_SPECIFIED].tolist() == [expected]


@pytest.mark.parametrize("abolish_council_tax", [False, True])
def test_ga_remains_a_unique_ordered_and_uprated_budget_term(abolish_council_tax):
    """Guardian cash belongs to both additive benefit-uprating groups."""
    from policyengine_uk.programs import (
        budget_programs,
        budget_variables,
        budget_variables_in_effect,
        uprated_benefit_variables,
    )

    terms = [p for p in budget_programs() if p.variable == "guardians_allowance"]
    assert len(terms) == 1
    term = terms[0]
    assert term.budget == "benefit"
    assert term.uprating == ("all", "non_sp")
    assert term.dropped_when is None
    order = budget_variables("benefit")
    assert order.count("guardians_allowance") == 1
    assert order.index("guardians_allowance") == order.index("child_benefit") + 1
    raw = yaml.safe_load((MODEL / "programs.yaml").read_text())
    assert raw["budget_order"]["benefit"] == order

    simulation = Simulation(
        situation=family([guardian(), child()]),
        reform={"gov.contrib.abolish_council_tax": abolish_council_tax},
    )
    active = budget_variables_in_effect(
        "benefit", simulation.tax_benefit_system.parameters(str(YEAR))
    )
    assert active.count("guardians_allowance") == 1
    for rate in ("all", "non_sp"):
        assert uprated_benefit_variables(active, rate).count("guardians_allowance") == 1


def test_ga_cash_is_counted_once_with_additive_budget_uprating():
    """The total adds £500 cash, £25 general and £50 non-pension uprating."""
    values = []
    for payment in (0, 500):
        simulation = Simulation(
            situation=family(
                [
                    guardian(
                        age=70,
                        private_pension_income=40_000,
                        miscellaneous_income=137,
                        guardians_allowance=payment,
                    ),
                    child(),
                ],
                benunit={"would_claim_uc": False},
            ),
            reform={
                "gov.contrib.benefit_uprating.all": 0.05,
                "gov.contrib.benefit_uprating.non_sp": 0.10,
            },
        )
        values.append(
            np.asarray(simulation.calculate("household_benefits", YEAR)).copy()
        )
    # Both selectors scale the original cash: 500 + 0.05 * 500 + 0.10 * 500.
    np.testing.assert_allclose(values[1] - values[0], [575], rtol=0, atol=0.01)


@pytest.mark.parametrize("year", [2028, 2030])
def test_future_computed_cash_projects_from_the_announced_2027_rate(year):
    """Annex A announces £23.75 for 2027–28; later years use CPI ratios.

    The index is the existing model projection, not a published future rate.
    Its five-decimal storage precision uses the shared CPI tests' weekly
    tolerance of one tenth of a penny; cash uses the existing penny tolerance.
    """
    situation = family(
        [guardian(guardians_allowance_full_rate_child_weeks=52), child()], year=year
    )
    for person in situation["people"].values():
        person.pop("guardians_allowance")
    simulation = Simulation(situation=situation)
    parameters = simulation.tax_benefit_system.parameters
    index = parameters.gov.benefit_uprating_cpi
    expected_weekly_rate = 23.75 * index(f"{year}-04-30") / index("2027-04-30")
    weekly_rate = parameters.gov.hmrc.guardians_allowance.weekly_rate(f"{year}-04-30")
    assert weekly_rate == pytest.approx(expected_weekly_rate, abs=1e-3)
    cash = simulation.calculate("guardians_allowance", year)
    np.testing.assert_allclose(cash, [52 * expected_weekly_rate, 0], rtol=0, atol=0.01)
