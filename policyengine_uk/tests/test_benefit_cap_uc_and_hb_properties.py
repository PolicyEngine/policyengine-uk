"""A family receiving both Universal Credit and Housing Benefit is capped once.

UC Regs 2013 reg 80(2A): where the welfare benefit is Housing Benefit, "the
amount to be used is nil". HB Regs 2006 reg 75F(1)(g): the Housing Benefit
cap does not apply where "the claimant is receiving universal credit". A
family paid Housing Benefit alongside Universal Credit (for specified or
temporary accommodation) is therefore capped only through Universal Credit,
on its other welfare benefits.

The model's Housing Benefit eligibility rules out a family that claims
Universal Credit (housing_benefit_eligible), so both awards are supplied here
as inputs (universal_credit_pre_benefit_cap, housing_benefit_pre_benefit_cap).

Invariants, for every family:

1. Housing Benefit changes no Universal Credit cap reduction: a family's
   reduction equals that of the same family with no Housing Benefit (reg
   80(2A)), and it is reg 81's excess over the cap, less the childcare
   element, of the welfare benefits without Housing Benefit.
2. Housing Benefit counts in the welfare benefits at its amount before the
   cap (HB Regs 2006 reg 75C(2)(b)): the total rises by exactly that amount.
3. A family receiving Universal Credit has no Housing Benefit reduction, and
   its benefit cap reduction is its Universal Credit reduction alone. If it
   has Housing Benefit, it is exempt from the Housing Benefit cap (reg
   75F(1)(g)).
4. A family without Universal Credit has no Universal Credit reduction, and
   its Housing Benefit reduction is reg 75D's: the excess over the Housing
   Benefit cap, leaving at least 50 pence a week.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2025
SINGLE_CAP = 14_753  # Outside London, 2025-26 (UC reg 80A(2); HB reg 75CA(2)).
HB_MINIMUM = 0.50 * 52  # HB Regs 2006 reg 75: 50 pence a week.

FAMILY = st.fixed_dictionaries(
    {
        "universal_credit": st.one_of(st.just(0), st.integers(1, 30_000)),
        "housing_benefit": st.integers(0, 20_000),
        "jsa_contrib": st.integers(0, 30_000),
        "childcare": st.integers(0, 10_000),
    }
)


def situation(families):
    """Each family twice: with its Housing Benefit, then with none."""
    people, benunits, households = {}, {}, {}
    units = [(f, f["housing_benefit"]) for f in families] + [(f, 0) for f in families]
    for i, (family, housing_benefit) in enumerate(units):
        person = f"p{i}"
        people[person] = {
            "age": {YEAR: 30},
            "is_claimant_or_partner": {YEAR: True},
            "jsa_contrib": {YEAR: family["jsa_contrib"]},
        }
        benunits[f"b{i}"] = {
            "members": [person],
            "universal_credit_pre_benefit_cap": {YEAR: family["universal_credit"]},
            "housing_benefit_pre_benefit_cap": {YEAR: housing_benefit},
            "uc_childcare_element": {YEAR: family["childcare"]},
        }
        households[f"h{i}"] = {
            "members": [person],
            "region": {YEAR: "NORTH_EAST"},
            "country": {YEAR: "ENGLAND"},
        }
    return {"people": people, "benunits": benunits, "households": households}


@settings(
    max_examples=12,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(st.lists(FAMILY, min_size=1, max_size=8))
def test_a_family_with_both_awards_is_capped_once_through_universal_credit(
    families,
):
    sim = Simulation(situation=situation(families))
    n = len(families)

    def calc(name):
        values = sim.calculate(name, YEAR)
        return values[:n], values[n:]

    uc, uc_without_hb = calc("uc_benefit_cap_reduction")
    hb_reduction, _ = calc("housing_benefit_benefit_cap_reduction")
    total_reduction, _ = calc("benefit_cap_reduction")
    welfare, welfare_without_hb = calc("benefit_cap_welfare_benefits")
    hb_exempt, _ = calc("is_housing_benefit_benefit_cap_exempt")
    uc_cap, _ = calc("uc_benefit_cap")
    hb_cap, _ = calc("housing_benefit_benefit_cap")

    on_uc = np.array([f["universal_credit"] > 0 for f in families])
    housing_benefit = np.array([f["housing_benefit"] for f in families], float)
    childcare = np.array([f["childcare"] for f in families], float)

    # 1. Reg 80(2A).
    np.testing.assert_allclose(uc, uc_without_hb, atol=0.01)
    assert (uc_cap == SINGLE_CAP).all()
    expected_uc = np.where(
        on_uc,
        np.maximum(
            np.maximum(welfare - housing_benefit - uc_cap, 0) - childcare,
            0,
        ),
        0,
    )
    np.testing.assert_allclose(uc, expected_uc, atol=0.01)

    # 2. Reg 75C(2)(b).
    np.testing.assert_allclose(welfare - welfare_without_hb, housing_benefit, atol=0.01)

    # 3. Reg 75F(1)(g).
    assert hb_exempt[on_uc & (housing_benefit > 0)].all()
    assert (hb_reduction[on_uc] == 0).all()
    np.testing.assert_allclose(total_reduction[on_uc], uc[on_uc], atol=0.01)

    # 4. Reg 75D for a family on Housing Benefit alone.
    off = ~on_uc
    assert (uc[off] == 0).all()
    assert (~hb_exempt[off]).all()
    assert (hb_cap[off] == SINGLE_CAP).all()
    expected_hb = np.minimum(
        np.maximum(welfare[off] - SINGLE_CAP, 0),
        np.maximum(housing_benefit[off] - HB_MINIMUM, 0),
    )
    np.testing.assert_allclose(hb_reduction[off], expected_hb, atol=0.01)
    np.testing.assert_allclose(total_reduction[off], expected_hb, atol=0.01)
