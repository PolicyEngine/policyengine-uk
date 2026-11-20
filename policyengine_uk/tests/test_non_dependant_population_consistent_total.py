"""Supplied cap totals that agree with each household's own calculation.

Each household's combined total and Housing Benefit come from its own
simulation with nothing supplied. Supplying both for a population of those
households gives every household the results it gets alone, whatever the
first request asks for. Supplying the totals without the Housing Benefit
raises ValueError (test_non_dependant_cycle_contracts.py states the
contract).
"""

import numpy as np
import pytest

from policyengine_uk import CountryTaxBenefitSystem
from policyengine_uk.tests.test_non_dependant_cycle_contracts import (
    FIRST_REQUESTS,
    YEAR,
    make,
    situation,
    supply,
)

HOUSEHOLDS = ["single", "nondep"]


@pytest.fixture(scope="module")
def system():
    return CountryTaxBenefitSystem()


@pytest.fixture(scope="module")
def standalone(system):
    """Each household's own totals and results, with nothing supplied."""
    results = {}
    for which in HOUSEHOLDS:
        sim = make(system, situation(which))
        units = list(situation(which)["benunits"])
        results[which] = {
            name: dict(zip(units, sim.calculate(name, YEAR).tolist()))
            for name in [
                "benefit_cap_welfare_benefits",
                "housing_benefit_pre_benefit_cap",
                "universal_credit",
                "housing_benefit",
            ]
        }
    return results


def consistent(standalone, *variables):
    """The mixed population with ``variables`` supplied at each household's
    own values."""
    data = situation("mixed")
    for variable in variables:
        values = {}
        for which in HOUSEHOLDS:
            values.update(standalone[which][variable])
        supply(data, variable, values)
    return data


def expected(standalone, name):
    return [value for which in HOUSEHOLDS for value in standalone[which][name].values()]


def test_each_household_alone(standalone):
    # The claimant pays no rent, so the total is the £20,000 of Universal
    # Credit; the applicant's total is their own Housing Benefit, before a
    # cap that pension age keeps away.
    assert expected(standalone, "benefit_cap_welfare_benefits") == pytest.approx(
        [20_000.0, 4_978.20, 0.0], abs=0.01
    )
    assert expected(standalone, "housing_benefit_pre_benefit_cap") == pytest.approx(
        [0.0, 4_978.20, 0.0], abs=0.01
    )
    assert expected(standalone, "universal_credit") == pytest.approx(
        [14_753.0, 0.0, 0.0], abs=0.01
    )


@pytest.mark.parametrize("first", FIRST_REQUESTS)
def test_consistent_totals_keep_households_independent(system, standalone, first):
    sim = make(
        system,
        consistent(
            standalone,
            "benefit_cap_welfare_benefits",
            "housing_benefit_pre_benefit_cap",
        ),
    )
    sim.calculate(first, YEAR)
    for name in ["universal_credit", "housing_benefit"]:
        np.testing.assert_allclose(
            sim.calculate(name, YEAR),
            expected(standalone, name),
            atol=0.01,
            err_msg=name,
        )


def test_consistent_totals_without_housing_benefit_raise(system, standalone):
    sim = make(system, consistent(standalone, "benefit_cap_welfare_benefits"))
    with pytest.raises(ValueError, match="housing_benefit_pre_benefit_cap"):
        sim.calculate("housing_benefit", YEAR)
