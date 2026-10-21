"""Savings Credit shares Pension Credit eligibility, not just its local age test.

The literal amounts use the existing 2026 model rates. The mixed-age case's
old positive amount is an off-route diagnostic, not lawful entitlement. The
positive controls reached pensionable age before April 2016; no protected
mixed-age Savings Credit continuity is inferred from reported Pension Credit.
"""

import numpy as np
import pytest

from policyengine_uk import Simulation
from policyengine_uk.variables.gov.dwp.pension_credit.savings_credit.savings_credit import (
    savings_credit,
)

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
YEAR = 2026


def situation():
    units = [
        ([(80, 20_000, 0), (60, 0, 0)], 6_240),
        ([(80, 9_000, 0), (78, 9_000, 0)], 6_240),
        ([(80, 11_000, 2_000)], 7_800),
        ([(40, 0, 0)], 6_240),
    ]
    people, benunits, households = {}, {}, {}
    for i, (adults, rent) in enumerate(units):
        names = []
        for j, (age, pension, private_pension) in enumerate(adults):
            name = f"p{i}_{j}"
            names.append(name)
            people[name] = {
                "age": {YEAR: age},
                "is_claimant_or_partner": {YEAR: True},
                "state_pension": {YEAR: pension},
                "private_pension_income": {YEAR: private_pension},
            }
        benunits[f"b{i}"] = {
            "members": names,
            "would_claim_pc": {YEAR: True},
            "would_claim_housing_benefit": {YEAR: True},
            "would_claim_uc": {YEAR: False},
        }
        households[f"h{i}"] = {
            "members": names,
            "country": {YEAR: "ENGLAND"},
            "local_authority": {YEAR: "MAIDSTONE"},
            "tenure_type": {YEAR: "RENT_FROM_COUNCIL"},
            "rent": {YEAR: rent},
            "council_tax": {YEAR: 2_000},
            "savings": {YEAR: 0},
        }
    return {"people": people, "benunits": benunits, "households": households}


def ungated_simulation():
    """Retain the former amount formula for a downstream differential control."""
    sim = Simulation(situation=situation())
    sim.tax_benefit_system.update_variable(
        type("savings_credit", (savings_credit,), {"defined_for": None})
    )
    return sim


@pytest.mark.parametrize("first", ["savings_credit", "pension_credit"])
def test_unprotected_mixed_age_savings_credit_is_zero(first):
    sim = Simulation(situation=situation())
    sim.calculate(first, YEAR)
    # The older member meets the local pre-2016 age condition, but the
    # unprotected younger partner excludes the couple from Pension Credit.
    assert sim.calculate("is_savings_credit_eligible", YEAR).tolist() == [
        True,
        True,
        True,
        False,
    ]
    assert sim.calculate("is_pension_credit_eligible", YEAR).tolist() == [
        False,
        True,
        True,
        False,
    ]
    # Couple: 0.6 * (18,000 - 329.75*52) = 511.80.
    # Single: 0.6*(238-208.07)*52 - 0.4*(12,914-238*52) = 718.616.
    np.testing.assert_allclose(
        sim.calculate("savings_credit", YEAR),
        [0, 511.80, 718.616, 0],
        atol=0.01,
        rtol=0,
    )


def test_shared_gate_preserves_final_pension_credit_and_consumers():
    fixed = Simulation(situation=situation())
    former = ungated_simulation()
    # The old off-route calculation was 0.6*(18,766-329.75*52) = 971.40, with the default married
    # couple receiving the existing Marriage Allowance of 1,260.
    assert former.calculate("savings_credit", YEAR)[0] == pytest.approx(
        971.40, abs=0.01
    )
    assert fixed.calculate("savings_credit", YEAR)[0] == 0
    consumers = [
        "guarantee_credit",
        "pension_credit_entitlement",
        "pension_credit",
        "in_receipt_of_savings_credit_only",
        "housing_benefit_applicable_income",
        "housing_benefit_assessable_capital",
        "housing_benefit_tariff_income",
        "housing_benefit",
        "council_tax_reduction_applicable_income",
        "council_tax_reduction_assessable_capital",
        "council_tax_reduction",
        "targeted_childcare_entitlement",
    ]
    for variable in consumers:
        np.testing.assert_allclose(
            fixed.calculate(variable, YEAR),
            former.calculate(variable, YEAR),
            atol=0.01,
            rtol=0,
            err_msg=variable,
        )
    # Both-old couple: Guarantee Credit 18,889-18,000 = 889, plus 511.80.
    for variable in ("pension_credit_entitlement", "pension_credit"):
        np.testing.assert_allclose(
            fixed.calculate(variable, YEAR),
            [0, 1_400.80, 718.616, 0],
            atol=0.01,
            rtol=0,
        )
    # The couple gets full rent on Guarantee Credit. The single's HB is
    # 7,800 - 0.65*(12,914+718.616-256*52) = 7,591.5996.
    np.testing.assert_allclose(
        fixed.calculate("housing_benefit", YEAR),
        [0, 6_240, 7_591.5996, 0],
        atol=0.01,
        rtol=0,
    )


def test_direct_savings_credit_input_keeps_its_existing_override_behavior():
    data = situation()
    data["benunits"]["b0"]["savings_credit"] = {YEAR: 123}
    sim = Simulation(situation=data)
    assert sim.calculate("savings_credit", YEAR)[0] == 123
    # An explicitly supplied component does not create a Pension Credit award.
    assert sim.calculate("pension_credit_entitlement", YEAR)[0] == 0
    assert sim.calculate("pension_credit", YEAR)[0] == 0
    assert sim.calculate("housing_benefit", YEAR)[0] == 0
