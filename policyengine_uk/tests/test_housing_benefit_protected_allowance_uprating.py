import pytest

from policyengine_uk import Simulation, system
from policyengine_uk.parameters.gov.dwp.housing_benefit.allowances.create_protected_pension_age_uprating import (
    project_retained_uplift,
)


def _parameters():
    return system.parameters


@pytest.mark.parametrize(
    (
        "allowance_name",
        "index_name",
        "base_allowance",
        "expected_2027_allowance",
    ),
    [
        ("single", "single", 256.0, 265.6622572049),
        ("lone_parent", "single", 256.0, 265.6622572049),
        ("couple", "couple", 383.35, 397.9411154524),
    ],
)
def test_protected_allowances_use_relationship_specific_component_projections(
    allowance_name,
    index_name,
    base_allowance,
    expected_2027_allowance,
):
    """The 2026 bases are guarantee plus retained Savings Credit uplift."""
    allowances = _parameters().gov.dwp.housing_benefit.allowances
    index = getattr(allowances.protected_pension_age_uprating, index_name)
    allowance = getattr(allowances, allowance_name).aged
    expected = base_allowance * index("2027-04-01") / index("2026-04-01")

    assert allowance("2026-04-01") == base_allowance
    assert expected == pytest.approx(expected_2027_allowance)
    assert allowance("2027-04-01") == pytest.approx(expected)
    assert allowance("2027-04-01") != pytest.approx(
        base_allowance
        * _parameters().gov.benefit_uprating_cpi("2027-04-01")
        / _parameters().gov.benefit_uprating_cpi("2026-04-01")
    )


def test_protected_allowances_cover_guarantee_and_maximum_savings_credit():
    parameters = _parameters()
    allowances = parameters.gov.dwp.housing_benefit.allowances
    pension_credit = parameters.gov.dwp.pension_credit
    guarantee = pension_credit.guarantee_credit.minimum_guarantee
    threshold = pension_credit.savings_credit.threshold

    for year in range(2027, 2040):
        instant = f"{year}-04-01"
        phase_in_rate = float(pension_credit.savings_credit.rate.phase_in(instant))
        for relationship, allowance_name in (
            ("SINGLE", "single"),
            ("COUPLE", "couple"),
        ):
            weekly_guarantee = float(getattr(guarantee, relationship)(instant))
            weekly_threshold = float(getattr(threshold, relationship)(instant))
            maximum_savings_credit = phase_in_rate * (
                weekly_guarantee - weekly_threshold
            )
            protected_allowance = float(
                getattr(allowances, allowance_name).aged(instant)
            )
            assert protected_allowance >= (
                weekly_guarantee + maximum_savings_credit - 0.01
            ), (relationship, year)


def test_retained_uplift_projection_does_not_reduce_the_cash_amount():
    assert project_retained_uplift(18, -0.02) == 18


def _boundary_calculation(couple: bool, private_pension: float) -> dict[str, float]:
    year = 2035
    names = ["claimant", "partner"] if couple else ["claimant"]
    people = {
        name: {
            "age": {year: 85},
            "private_pension_income": {
                year: private_pension if name == "claimant" else 0
            },
        }
        for name in names
    }
    simulation = Simulation(
        situation={
            "people": people,
            "benunits": {"benunit": {"members": names}},
            "households": {
                "household": {
                    "members": names,
                    "country": {year: "ENGLAND"},
                    "local_authority": {year: "MAIDSTONE"},
                    "tenure_type": {year: "RENT_FROM_COUNCIL"},
                    "rent": {year: 10_000},
                    "council_tax": {year: 2_000},
                    "savings": {year: 0},
                }
            },
        }
    )
    return {
        variable: float(simulation.calculate(variable, year)[0])
        for variable in (
            "guarantee_credit",
            "housing_benefit",
            "council_tax_benefit",
            "household_net_income",
            "tv_licence",
        )
    }


@pytest.mark.parametrize(
    ("couple", "income_below", "income_above"),
    [(False, 16_808, 16_809), (True, 27_133, 27_134)],
)
def test_net_income_does_not_fall_when_guarantee_credit_ends(
    couple,
    income_below,
    income_above,
):
    """Test £1 income steps across each modeled 2035 guarantee boundary.

    A normal marginal withdrawal may occur, but there must be no discontinuous
    loss of Housing Benefit or Council Tax Reduction when Guarantee Credit ends.
    """
    below = _boundary_calculation(couple, income_below)
    above = _boundary_calculation(couple, income_above)

    assert below["guarantee_credit"] > 0
    assert above["guarantee_credit"] == 0
    assert above["housing_benefit"] >= below["housing_benefit"] - 1
    assert above["council_tax_benefit"] >= below["council_tax_benefit"] - 1
    assert above["household_net_income"] + above["tv_licence"] >= (
        below["household_net_income"] + below["tv_licence"] - 0.01
    )
