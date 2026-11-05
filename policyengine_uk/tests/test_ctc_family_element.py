"""Family-only DOB eligibility and its inherited annual/input contracts.

SI 2002/2007 reg 7(2)(a), amended by SI 2017/387 reg 4(b), requires a
responsible child/QYP born strictly before 6 April 2017. The 2024 cash
oracles use unchanged child3455/family545, zero income and a reported
continuing claim. They do not audit daily statutory award rounding.
"""

from pathlib import Path

import pytest

from policyengine_core.parameters.helpers import load_parameter_file
from policyengine_uk import CountryTaxBenefitSystem, Simulation

PREFIX = "gov.dwp.tax_credits.child_tax_credit.eligibility."


def situation(children, year=2024, parent=None, benunit_inputs=None):
    facts = {"parent": {"age": 35, "child_tax_credit_reported": 1}}
    facts["parent"].update(parent or {})
    facts.update(children)
    people = {
        name: {key: {year: value} for key, value in person.items()}
        for name, person in facts.items()
    }
    members = list(people)
    return {
        "people": people,
        "benunits": {
            "family": {
                "members": members,
                "would_claim_uc": {year: False},
                **{key: {year: value} for key, value in (benunit_inputs or {}).items()},
            }
        },
        "households": {"home": {"members": members}},
    }


def child(born=20170406, age=7, **other):
    return {"child": {"age": age, "date_of_birth": born, **other}}


def assert_cash(sim, expected, year=2024):
    assert sim.calculate("child_tax_credit", year)[0] == pytest.approx(
        expected, abs=0.01
    )
    assert sim.calculate("tax_credits", year)[0] == pytest.approx(expected, abs=0.01)


def test_raw_commencement_and_annual_mapping_preserve_prior_supported_years():
    root = Path(__file__).resolve().parents[1] / "parameters"
    applies = load_parameter_file(
        str(
            root
            / "gov/dwp/tax_credits/child_tax_credit/eligibility/family_element_birth_date_condition_applies.yaml"
        ),
        name="applies",
    )
    cutoff = load_parameter_file(
        str(
            root
            / "gov/dwp/tax_credits/child_tax_credit/eligibility/family_element_born_before.yaml"
        ),
        name="cutoff",
    )
    assert (
        applies("2015-01-01") is False
    )  # Existing coverage anchor, not legal commencement.
    assert applies("2017-04-05") is False
    assert applies("2017-04-06") is True
    assert cutoff.values_list[-1].instant_str == "2017-04-06"
    assert cutoff("2017-04-06") == 20170406
    system = CountryTaxBenefitSystem()
    for year, expected in [(2015, False), (2016, False), (2017, True), (2024, True)]:
        p = system.parameters(
            str(year)
        ).gov.dwp.tax_credits.child_tax_credit.eligibility
        assert p.family_element_birth_date_condition_applies == expected


@pytest.mark.parametrize("year", [2015, 2016])
def test_prior_supported_years_keep_the_existing_flat_family_element(year):
    sim = Simulation(situation=situation(child((year - 1) * 10000 + 406, 1), year))
    assert sim.calculate("CTC_family_element", year)[0] == 545


def test_annual_2017_uses_the_qualified_april_condition():
    sim = Simulation(situation=situation(child(20170406, 0), 2017))
    assert_cash(sim, 2780, 2017)  # Unchanged 2017 child-element baseline; family0.
    assert sim.calculate("CTC_family_element", 2017)[0] == 0


def test_a_genuine_qualifying_young_person_can_unlock_the_family_element():
    sim = Simulation(
        situation=situation(
            child(20060901, 18, current_education="UPPER_SECONDARY"), parent={"age": 45}
        )
    )
    assert sim.calculate(
        "is_child_or_qualifying_young_person_for_child_tax_credit", 2024
    ).tolist() == [False, True]
    assert_cash(sim, 4000)


def test_an_older_excluded_member_cannot_unlock_a_younger_childs_family_element():
    # Existing looked-after proxy excludes the older child; its wider legal
    # limitations are unchanged. Adult claimants are also outside the mask.
    sim = Simulation(
        situation=situation(
            {
                "older": {
                    "age": 10,
                    "date_of_birth": 20140405,
                    "is_looked_after_by_local_authority": True,
                },
                **child(),
            },
            parent={"age": 40},
        )
    )
    assert sim.calculate(
        "is_child_or_qualifying_young_person_for_child_tax_credit", 2024
    ).tolist() == [False, False, True]
    assert_cash(sim, 3455)
    assert sim.calculate("CTC_family_element", 2024)[0] == 0


def test_multiple_qualifying_children_receive_one_flat_family_amount():
    sim = Simulation(
        situation=situation(
            {
                "older": {"age": 10, "date_of_birth": 20140405},
                "younger": {"age": 8, "date_of_birth": 20160405},
            }
        )
    )
    assert_cash(sim, 7455)  # 2 * 3455 + one545, not545perchild.
    assert sim.calculate("CTC_family_element", 2024)[0] == 545


@pytest.mark.parametrize("months,expected", [(5, 3455), (6, 3455), (7, 4000)])
def test_partial_dob_inputs_retain_the_existing_annual_age_fallback(months, expected):
    sim = Simulation(
        situation=situation(
            child(0, 7, months_since_last_birthday=months),
            parent={"date_of_birth": 19890101},
        )
    )
    assert_cash(sim, expected)


def test_birth_year_override_does_not_replace_the_existing_dob_helper():
    sim = Simulation(situation=situation(child(0, 7, birth_year=2000)))
    assert_cash(sim, 3455)


@pytest.mark.parametrize(
    "born,cutoff,expected,individual_exempt",
    [(20170406, 20170407, 4000, False), (20170405, 20170405, 3455, True)],
)
def test_family_cutoff_reforms_do_not_move_the_individual_element_cutoff(
    born, cutoff, expected, individual_exempt
):
    sim = Simulation(
        situation=situation(child(born)),
        reform={PREFIX + "family_element_born_before": cutoff},
    )
    assert_cash(sim, expected)
    assert (
        bool(sim.calculate("is_CTC_child_limit_exempt", 2024)[1]) is individual_exempt
    )


def test_family_activation_is_independently_reformable():
    sim = Simulation(
        situation=situation(child()),
        reform={PREFIX + "family_element_birth_date_condition_applies": False},
    )
    assert_cash(sim, 4000)


def test_individual_element_exception_does_not_waive_the_family_condition():
    sim = Simulation(
        situation=situation(child()),
        reform={"gov.contrib.two_child_limit.age_exemption.child_tax_credit": 10},
    )
    assert bool(sim.calculate("is_CTC_child_limit_exempt", 2024)[1])
    assert_cash(sim, 3455)
    assert sim.calculate("CTC_family_element", 2024)[0] == 0


@pytest.mark.parametrize("reverse", [False, True])
def test_family_boundaries_are_local_across_units_member_and_request_order(reverse):
    people, benunits = {}, {}
    for name, born in [("before", 20170405), ("on", 20170406)]:
        inputs = situation(child(born))
        names = [name + "_parent", name + "_child"]
        people.update(
            {new: value for new, value in zip(names, inputs["people"].values())}
        )
        benunits[name] = {
            "members": names[::-1] if reverse else names,
            "would_claim_uc": {2024: False},
        }
    if reverse:
        people = dict(reversed(list(people.items())))
        benunits = dict(reversed(list(benunits.items())))
    sim = Simulation(
        situation={
            "people": people,
            "benunits": benunits,
            "households": {"shared": {"members": list(people)}},
        }
    )
    if reverse:
        sim.calculate("is_CTC_child_limit_exempt", 2024)
        sim.calculate("CTC_family_element", 2024)
    for variable in ["child_tax_credit", "tax_credits"]:
        values = dict(
            zip(sim.populations["benunit"].ids, sim.calculate(variable, 2024))
        )
        assert values == pytest.approx({"before": 4000, "on": 3455}, abs=0.01)


@pytest.mark.parametrize(
    "variable,amount", [("CTC_family_element", 123), ("child_tax_credit", 222)]
)
def test_explicit_amount_inputs_remain_overrides_not_entitlement_proof(
    variable, amount
):
    sim = Simulation(situation=situation(child(), benunit_inputs={variable: amount}))
    assert sim.calculate(variable, 2024)[0] == amount
    if variable == "CTC_family_element":
        assert_cash(sim, 3578)  # 3455 + explicitly supplied123.


def test_scheme_closure_still_overrides_an_old_childs_family_qualification():
    sim = Simulation(situation=situation(child(20170405, 8), 2025))
    assert_cash(sim, 0, 2025)
