"""Universal Credit against Tax-Free Childcare, and debt deductions on awards
that only a reform creates (#2753, #2689).

Cutting the Universal Credit taper from 55% to 50% left some families worse
off: a first, small award ended their Tax-Free Childcare, and a deduction
drawn for the existing caseload took part of that award. A family better off
with the top-up does not claim, and a new award carries no old debts."""

import numpy as np
import pytest
from policyengine_core.periods import period

from policyengine_uk import Simulation

YEAR = 2027
TAPER_CUT = {
    "gov.dwp.universal_credit.means_test.reduction_rate": {
        "2027-01-01.2100-12-31": 0.50
    }
}
# A 15% latent deduction rate, all advance repayments, as a dataset supplies,
# with the incidence draw that assigns it: the rate counts only where
# uc_has_deduction is true (#2739), and 0.2 falls below London's incidence.
DEDUCTION = {
    "uc_deduction_random_draw": {YEAR: 0.2},
    "uc_latent_deduction_rate": {YEAR: 0.15},
    "uc_deduction_combination": {YEAR: "ADVANCE_ONLY"},
}


def couple_with_childcare(
    earnings_each, name="", region="LONDON", child=None, **benunit
):
    """People, benefit unit and household of a couple in ``region`` renting
    privately for £24,000 a year, each earning ``earnings_each``, with
    children aged 3 and 6 in £6,000 of childcare each: £2,400 of
    Tax-Free Childcare a year. ``child`` adds inputs to both children."""
    adults = [f"adult1{name}", f"adult2{name}"]
    children = [f"child1{name}", f"child2{name}"]
    child = child or {}
    people = {
        **{
            a: {"age": {YEAR: 35}, "employment_income": {YEAR: earnings_each}}
            for a in adults
        },
        children[0]: {
            "age": {YEAR: 3},
            "childcare_expenses": {YEAR: 6_000.0},
            **child,
        },
        children[1]: {
            "age": {YEAR: 6},
            "childcare_expenses": {YEAR: 6_000.0},
            **child,
        },
    }
    members = adults + children
    household = {
        "members": members,
        "region": {YEAR: region},
        "rent": {YEAR: 24_000.0},
        "tenure_type": {YEAR: "RENT_PRIVATELY"},
    }
    return people, {"members": members, **benunit}, household


def situation(*families):
    result = {"people": {}, "benunits": {}, "households": {}}
    for i, (people, benunit, household) in enumerate(families):
        result["people"].update(people)
        result["benunits"][f"benunit{i}"] = benunit
        result["households"][f"household{i}"] = household
    return result


def values(sim, variable):
    return np.asarray(sim.calculate(variable, YEAR))


@pytest.mark.parametrize("earnings", [58_000.0, 59_500.0, 60_000.0, 63_000.0])
@pytest.mark.parametrize("deduction", [{}, DEDUCTION], ids=["none", "latent"])
def test_taper_cut_leaves_tax_free_childcare_families_no_worse_off(earnings, deduction):
    """#2753: with and without a deduction, across the earnings where the
    cut used to give a first award worth less than Tax-Free Childcare or a
    deduction that took it below."""
    case = situation(couple_with_childcare(earnings, **deduction))
    baseline = Simulation(situation=case)
    reform = Simulation(situation=case, reform=TAPER_CUT)
    gain = values(reform, "household_net_income") - values(
        baseline, "household_net_income"
    )
    assert gain[0] >= -0.01


def test_an_award_worth_less_than_tax_free_childcare_is_forgone():
    # The cut gives £1,993 against £2,400 of Tax-Free Childcare.
    reform = Simulation(
        situation=situation(couple_with_childcare(60_000.0)), reform=TAPER_CUT
    )
    assert values(reform, "forgoes_universal_credit_for_tax_free_childcare")[0]
    assert values(reform, "universal_credit")[0] == 0
    assert values(reform, "tax_free_childcare").sum() == pytest.approx(2_400)


def test_an_award_worth_more_than_tax_free_childcare_is_claimed():
    # The cut gives £3,153 against £2,400 of Tax-Free Childcare.
    reform = Simulation(
        situation=situation(couple_with_childcare(58_000.0)), reform=TAPER_CUT
    )
    assert not values(reform, "forgoes_universal_credit_for_tax_free_childcare")[0]
    assert values(reform, "universal_credit")[0] == pytest.approx(3_153, abs=1)
    assert values(reform, "tax_free_childcare").sum() == 0


def test_a_small_award_under_current_law_is_forgone():
    # At £56,000 each the 55% taper leaves an award of about £274.
    sim = Simulation(situation=situation(couple_with_childcare(56_000.0)))
    assert values(sim, "forgoes_universal_credit_for_tax_free_childcare")[0]
    assert values(sim, "universal_credit")[0] == 0
    assert values(sim, "tax_free_childcare").sum() == pytest.approx(2_400)


def test_no_deduction_comes_out_of_an_award_only_the_reform_creates():
    case = situation(couple_with_childcare(58_000.0, **DEDUCTION))
    baseline = Simulation(situation=case)
    reform = Simulation(situation=case, reform=TAPER_CUT)
    assert values(baseline, "universal_credit_pre_benefit_cap")[0] == 0
    assert values(reform, "universal_credit_pre_benefit_cap")[0] > 0
    assert not values(reform, "uc_award_carries_deductions")[0]
    assert values(reform, "uc_deductions")[0] == 0
    assert values(reform, "uc_benefit_cap_reduction_after_floor")[0] == 0


def test_the_engine_draw_gives_no_deduction_on_an_award_only_the_reform_creates():
    case = situation(
        couple_with_childcare(58_000.0, uc_deduction_random_draw={YEAR: 0.2})
    )
    reform = Simulation(situation=case, reform=TAPER_CUT)
    assert not values(reform, "uc_has_deduction")[0]
    assert values(reform, "uc_deductions")[0] == 0


def test_an_existing_award_keeps_its_deduction_under_the_reform():
    case = situation(couple_with_childcare(40_000.0, **DEDUCTION))
    baseline = Simulation(situation=case)
    reform = Simulation(situation=case, reform=TAPER_CUT)
    deduction = values(baseline, "uc_deductions")[0]
    assert deduction > 0
    assert values(reform, "uc_deductions")[0] == pytest.approx(deduction)


def apply_taper_cut_as_a_modifier(sim):
    """What policyengine.py's _apply_step does with a policy that has only a
    simulation modifier: change the built simulation's parameters, then drop
    what it calculated."""
    sim.tax_benefit_system.parameters.get_child(
        "gov.dwp.universal_credit.means_test.reduction_rate"
    ).update(value=0.50, start=period("2027-01-01"), stop=None)
    sim.drop_computed_arrays()


def test_a_reform_applied_as_a_modifier_is_compared_with_the_baseline():
    """The same taper cut reaching the simulation after it is built."""
    case = situation(couple_with_childcare(58_000.0, **DEDUCTION))
    baseline = Simulation(situation=case)
    reform = Simulation(situation=case)
    apply_taper_cut_as_a_modifier(reform)
    assert reform.changed_from_baseline
    assert values(reform, "universal_credit_pre_benefit_cap")[0] > 0
    assert values(reform, "uc_deductions")[0] == 0
    gain = (
        values(reform, "household_net_income")[0]
        - values(baseline, "household_net_income")[0]
    )
    assert gain == pytest.approx(752.66, abs=0.01)


def test_a_reform_applied_after_the_simulation_is_built_is_compared():
    reform = Simulation(
        situation=situation(couple_with_childcare(58_000.0, **DEDUCTION))
    )
    assert not reform.changed_from_baseline
    reform.apply_reform(TAPER_CUT)
    assert reform.changed_from_baseline
    assert values(reform, "universal_credit_pre_benefit_cap")[0] > 0
    assert values(reform, "uc_deductions")[0] == 0


def test_a_current_law_simulation_is_not_compared_with_its_baseline():
    """Its baseline is a copy of itself. A bare set_input does not count as a
    change, so an award it makes keeps its deduction, and the copy works out
    no Universal Credit."""
    sim = Simulation(situation=situation(couple_with_childcare(58_000.0, **DEDUCTION)))
    assert not sim.changed_from_baseline
    sim.set_input("employment_income", YEAR, np.array([40_000.0, 40_000.0, 0, 0]))
    assert values(sim, "universal_credit_pre_benefit_cap")[0] > 0
    assert values(sim, "uc_award_carries_deductions")[0]
    assert values(sim, "uc_deductions")[0] > 0
    holder = sim.baseline.get_holder("universal_credit_pre_benefit_cap")
    assert holder.get_known_periods() == []


def test_the_scottish_child_payment_a_claim_brings_is_weighed():
    """In Scotland any award qualifies the children for Scottish Child
    Payment. At £45,000 each the £1,571 award brings £3,037 of it, together
    worth more than £2,400 of Tax-Free Childcare."""
    sim = Simulation(
        situation=situation(couple_with_childcare(45_000.0, region="SCOTLAND"))
    )
    assert not values(sim, "forgoes_universal_credit_for_tax_free_childcare")[0]
    assert values(sim, "universal_credit")[0] == pytest.approx(1_571, abs=1)
    assert values(sim, "scottish_child_payment").sum() == pytest.approx(3_037, abs=1)
    assert values(sim, "tax_free_childcare").sum() == 0


def test_an_award_is_forgone_in_scotland_when_the_payment_is_not_claimed():
    sim = Simulation(
        situation=situation(
            couple_with_childcare(
                45_000.0, region="SCOTLAND", child={"would_claim_scp": {YEAR: False}}
            )
        )
    )
    assert values(sim, "forgoes_universal_credit_for_tax_free_childcare")[0]
    assert values(sim, "universal_credit")[0] == 0
    assert values(sim, "tax_free_childcare").sum() == pytest.approx(2_400)


def test_households_with_and_without_a_baseline_award_in_one_simulation():
    """The baseline award is worked out in a branch of the baseline holding
    only the households with an award, so mix the cases."""
    case = situation(
        couple_with_childcare(58_000.0, name="new", **DEDUCTION),
        couple_with_childcare(40_000.0, name="existing", **DEDUCTION),
        couple_with_childcare(100_000.0, name="none", **DEDUCTION),
    )
    baseline = Simulation(situation=case)
    reform = Simulation(situation=case, reform=TAPER_CUT)
    assert list(values(reform, "uc_award_carries_deductions")) == [False, True, True]
    deductions = values(reform, "uc_deductions")
    assert deductions[0] == 0
    assert deductions[1] == pytest.approx(values(baseline, "uc_deductions")[1])
    assert deductions[1] > 0
    assert deductions[2] == 0
