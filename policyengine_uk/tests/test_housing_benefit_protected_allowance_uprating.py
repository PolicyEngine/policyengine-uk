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
        ("single", "single", 256.0, 265.9113772049),
        ("lone_parent", "lone_parent", 256.0, 265.9113772049),
        ("couple", "couple", 383.35, 398.2192994524),
    ],
)
def test_protected_allowances_use_relationship_specific_component_projections(
    allowance_name,
    index_name,
    base_allowance,
    expected_2027_allowance,
):
    """The 2026 bases are guarantee plus retained Savings Credit uplift.

    The retained uplift rises by September 2026 CPI, 3.5% (ONS, 21 October
    2026); the guarantee by the statutory earnings floor.
    """
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


def _boundary_simulation(couple: bool, private_pension: float) -> Simulation:
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
    return Simulation(
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


def _boundary_calculation(couple: bool, private_pension: float) -> dict[str, float]:
    simulation = _boundary_simulation(couple, private_pension)
    return {
        variable: float(simulation.calculate(variable, 2035)[0])
        for variable in (
            "guarantee_credit",
            "housing_benefit",
            "council_tax_benefit",
            "household_net_income",
            "tv_licence",
        )
    }


@pytest.mark.parametrize("couple", [False, True])
def test_net_income_does_not_fall_when_guarantee_credit_ends(couple):
    """Test £1 income steps across each modeled 2035 guarantee boundary.

    A normal marginal withdrawal may occur, but there must be no discontinuous
    loss of Housing Benefit or Council Tax Reduction when Guarantee Credit ends.
    """
    # Locate the actual cutoff, including income-tax deductions. Forecasts and
    # tax thresholds can change independently of this discontinuity regression.
    income_below, income_above = 0, 100_000
    assert (
        _boundary_simulation(couple, income_below).calculate("guarantee_credit", 2035)[
            0
        ]
        > 0
    )
    assert (
        _boundary_simulation(couple, income_above).calculate("guarantee_credit", 2035)[
            0
        ]
        == 0
    )
    while income_above - income_below > 1:
        midpoint = (income_below + income_above) // 2
        if (
            _boundary_simulation(couple, midpoint).calculate("guarantee_credit", 2035)[
                0
            ]
            > 0
        ):
            income_below = midpoint
        else:
            income_above = midpoint

    below = _boundary_calculation(couple, income_below)
    above = _boundary_calculation(couple, income_above)

    assert below["guarantee_credit"] > 0
    assert above["guarantee_credit"] == 0
    assert above["housing_benefit"] >= below["housing_benefit"] - 1
    assert above["council_tax_benefit"] >= below["council_tax_benefit"] - 1
    assert above["household_net_income"] + above["tv_licence"] >= (
        below["household_net_income"] + below["tv_licence"] - 0.01
    )


@pytest.mark.parametrize(
    ("allowance_name", "weekly_amount"),
    [("single", 244.40), ("lone_parent", 244.40), ("couple", 366.00)],
)
def test_protected_allowances_match_enacted_2025_amounts(allowance_name, weekly_amount):
    """Pin the published protected-cohort rates, not a computed CPI estimate.

    SI 2025/295 Sch 6 and NI SR 2025/64 Sch 6, table paras 1(1)(b)
    and 1(2)(b), prescribe these amounts independently of the model.
    """
    allowance = getattr(
        _parameters().gov.dwp.housing_benefit.allowances, allowance_name
    ).aged
    assert allowance("2025-04-30") == weekly_amount


@pytest.mark.parametrize(
    ("allowance_name", "relationship"),
    [("single", "SINGLE"), ("lone_parent", "SINGLE"), ("couple", "COUPLE")],
)
def test_later_cohort_allowances_equal_the_guarantee_in_every_year(
    allowance_name, relationship
):
    """The allowances for those reaching State Pension age from April 2021
    equal the standard minimum guarantee in every enacted year (SI 2006/214
    Sch 3 para 1(1)(c) and (2)(c)), and project by the same earnings index,
    so they stay equal."""
    parameters = _parameters()
    allowance = getattr(
        parameters.gov.dwp.housing_benefit.allowances, allowance_name
    ).aged_from_cutoff
    guarantee = getattr(
        parameters.gov.dwp.pension_credit.guarantee_credit.minimum_guarantee,
        relationship,
    )
    for year in range(2021, 2041):
        instant = f"{year}-04-30"
        assert allowance(instant) == pytest.approx(guarantee(instant)), year
