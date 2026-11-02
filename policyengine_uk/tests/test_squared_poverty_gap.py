"""FGT2 components and person-weighted aggregation on tiny synthetic data.

The .7 oracle differs from a .5 household-weighted mean: one person carries
weight2 and component.25; three people each carry weight1 and component1.
These are technical fixtures, not representative population estimates.
"""

import numpy as np
import pytest

from policyengine_uk import CountryTaxBenefitSystem, Microsimulation, Simulation


YEAR = 2025


def situation(sizes, weights, lines, incomes):
    people, families, households = {}, {}, {}
    for h, (size, weight, line, income) in enumerate(
        zip(sizes, weights, lines, incomes)
    ):
        members = [f"h{h}_p{i}" for i in range(size)]
        for i, person in enumerate(members):
            people[person] = {"age": {YEAR: 40 if i == 0 else 8}}
        families[f"family{h}"] = {"members": members}
        households[f"home{h}"] = {
            "members": members,
            "household_weight": {YEAR: weight},
            "hbai_household_net_income_before_reset_to_zero": {YEAR: income},
            "poverty_line_bhc": {YEAR: line},
            "poverty_line_ahc": {YEAR: line},
        }
    return {"people": people, "benunits": families, "households": households}


@pytest.mark.parametrize("basis", ["bhc", "ahc"])
def test_person_mapped_weighted_mean_differs_from_household_mean(basis):
    sim = Microsimulation(situation=situation([1, 3], [2, 1], [100, 100], [50, 0]))
    variable = f"squared_poverty_gap_{basis}"
    component = sim.calculate(variable, YEAR, map_to="person")
    np.testing.assert_allclose(component, [0.25, 1, 1, 1])
    np.testing.assert_allclose(component.weights, [2, 1, 1, 1])
    assert component.mean(skipna=False) == pytest.approx(0.7)
    assert sim.calculate(variable, YEAR).mean(skipna=False) == pytest.approx(0.5)


@pytest.mark.parametrize("basis", ["bhc", "ahc"])
def test_undefined_household_is_not_dropped_from_person_mean(basis):
    sim = Microsimulation(situation=situation([1, 3], [2, 1], [100, 0], [50, 0]))
    with np.errstate(all="raise"):
        component = sim.calculate(f"squared_poverty_gap_{basis}", YEAR, map_to="person")
    assert component.iloc[0] == 0.25
    assert np.isnan(component.iloc[1:]).all()
    assert np.isnan(component.mean(skipna=False))


@pytest.mark.parametrize("basis", ["bhc", "ahc"])
def test_mixed_positive_zero_negative_lines_do_not_emit_division_warnings(basis):
    sim = Simulation(
        situation=situation(
            [1, 1, 1, 1], [1, 1, 1, 1], [100, 0, -100, 200], [50, 0, 0, 100]
        )
    )
    with np.errstate(all="raise"):
        component = sim.calculate(f"squared_poverty_gap_{basis}", YEAR)
    np.testing.assert_allclose(component, [0.25, np.nan, np.nan, 0.25], equal_nan=True)


def test_components_are_annual_dimensionless_household_variables_without_alias():
    system = CountryTaxBenefitSystem()
    for basis in ["bhc", "ahc"]:
        variable = system.get_variable(f"squared_poverty_gap_{basis}")
        assert variable is not None
        assert variable.entity.key == "household"
        assert str(variable.definition_period) == "year"
        assert variable.unit == "/1"
    assert "squared_poverty_gap" not in system.variables
