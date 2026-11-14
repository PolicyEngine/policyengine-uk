"""Childcare Grant costs on children must reach final household totals."""

import pytest

from policyengine_uk import Simulation
from policyengine_uk.utils.scenario import Scenario


pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")


def test_child_cost_coverage_change_reaches_final_household_totals():
    """Reg. 45/SFE 2025-26: 85% of GBP5,000 is GBP4,250, below the cap."""
    situation = {
        "people": {
            "person1": {
                "age": {2025: 24},
                "is_parent": {2025: True},
                "current_education": {2025: "TERTIARY"},
                "childcare_grant_full_time_student": {2025: True},
            },
            "person2": {
                "age": {2025: 4},
                "childcare_expenses": {2025: 5_000},
            },
        },
        "benunits": {"benunit": {"members": ["person1", "person2"]}},
        "households": {
            "household": {
                "members": ["person1", "person2"],
                "country": {2025: "ENGLAND"},
            }
        },
    }
    baseline = Simulation(situation=situation)
    # Deliberate diagnostic control, not a claim about a statutory 50% rate:
    # 5,000 * 50% = 2,500; the final aggregates must differ by 1,750.
    fifty_percent_control = Simulation(
        situation=situation,
        scenario=Scenario(
            parameter_changes={"gov.dfe.childcare_grant.coverage_rate": {2025: 0.5}}
        ),
    )

    assert baseline.calculate("childcare_grant_eligible", 2025).tolist() == [
        True,
        False,
    ]
    assert baseline.calculate("childcare_grant", 2025).tolist() == pytest.approx(
        [4_250, 0], abs=0.01
    )
    assert fifty_percent_control.calculate("childcare_grant", 2025).tolist() == (
        pytest.approx([2_500, 0], abs=0.01)
    )
    for variable in ("household_benefits", "gov_spending", "hbai_benefits"):
        difference = baseline.calculate(
            variable, 2025
        ) - fifty_percent_control.calculate(variable, 2025)
        assert difference.tolist() == pytest.approx([1_750], abs=0.01), variable
