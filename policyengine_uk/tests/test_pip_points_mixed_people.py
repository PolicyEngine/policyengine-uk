"""PIP categories are decided per person when some people have points.

One person's points are not evidence about anyone else, so a person given
only an earlier category keeps it in a year when someone else has points.
"""

import pytest

from policyengine_uk import Simulation


def _two_adults(first_person: dict, second_person: dict) -> dict:
    """Two adults aged 30 in separate benefit units and households in London."""
    people = {"a": first_person, "b": second_person}
    situation = {
        "people": {},
        "benunits": {},
        "households": {},
    }
    for name, inputs in people.items():
        situation["people"][name] = {"age": {"2025": 30, "2026": 31}, **inputs}
        situation["benunits"][f"benunit_{name}"] = {"members": [name]}
        situation["households"][f"household_{name}"] = {
            "members": [name],
            "region": {"2025": "LONDON", "2026": "LONDON"},
        }
    return situation


@pytest.mark.parametrize(
    "component, points_variable, category_variable, amount_variable, "
    "enhanced_2025, enhanced_2026",
    [
        ("daily living", "pip_dl_points", "pip_dl_category", "pip", 5_740.80, 5_959.20),
        ("mobility", "pip_m_points", "pip_m_category", "pip", 4_006.60, 4_160.00),
    ],
)
def test_one_persons_points_keep_anothers_carried_category(
    component,
    points_variable,
    category_variable,
    amount_variable,
    enhanced_2025,
    enhanced_2026,
):
    # A is assessed at 12 points in 2026. B has only an enhanced award from
    # 2025 and no points in any year.
    simulation = Simulation(
        situation=_two_adults(
            {points_variable: {"2026": 12}},
            {category_variable: {"2025": "ENHANCED"}},
        )
    )
    categories = {
        year: list(simulation.calculate(category_variable, year))
        for year in (2025, 2026)
    }
    assert categories == {
        2025: ["NONE", "ENHANCED"],
        2026: ["ENHANCED", "ENHANCED"],
    }, component
    assert simulation.calculate(amount_variable, 2025).tolist() == pytest.approx(
        [0, enhanced_2025], abs=0.05
    )
    assert simulation.calculate(amount_variable, 2026).tolist() == pytest.approx(
        [enhanced_2026, enhanced_2026], abs=0.05
    )


def test_supplied_zero_points_still_replace_an_earlier_category():
    # Zero points are an assessment, unlike points left out.
    simulation = Simulation(
        situation=_two_adults(
            {
                "pip_dl_category": {"2025": "ENHANCED"},
                "pip_dl_points": {"2026": 0},
            },
            {"pip_dl_category": {"2025": "ENHANCED"}},
        )
    )
    assert list(simulation.calculate("pip_dl_category", 2026)) == [
        "NONE",
        "ENHANCED",
    ]


def test_a_persons_earlier_points_carry_forward_past_anothers_later_points():
    # B was assessed at 12 points in 2025; A is assessed in 2026 and B is not.
    simulation = Simulation(
        situation=_two_adults(
            {"pip_dl_points": {"2026": 12}},
            {"pip_dl_points": {"2025": 12}},
        )
    )
    assert list(simulation.calculate("pip_dl_category", 2026)) == [
        "ENHANCED",
        "ENHANCED",
    ]
    assert simulation.calculate("pip", 2026).tolist() == pytest.approx(
        [5_959.20, 5_959.20], abs=0.05
    )


def test_a_persons_later_points_beat_their_own_earlier_category_only():
    # A had an enhanced award in 2025 and scores 8 points in 2026. B keeps
    # their own 2025 standard award.
    simulation = Simulation(
        situation=_two_adults(
            {
                "pip_m_category": {"2025": "ENHANCED"},
                "pip_m_points": {"2026": 8},
            },
            {"pip_m_category": {"2025": "STANDARD"}},
        )
    )
    assert list(simulation.calculate("pip_m_category", 2026)) == [
        "STANDARD",
        "STANDARD",
    ]
