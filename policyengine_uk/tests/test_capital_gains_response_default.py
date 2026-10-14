"""The default capital gains realisation response (issue #2396).

Realised gains respond to a reform at a retention-rate elasticity of 1:
G1 = G0 x ((1 - t1) / (1 - t0)), with t0 and t1 the person's baseline and
reform marginal rates measured at the same gains before the response. Gains
qualifying for Business Asset Disposal Relief take the same elasticity.

These tests check the default against an explicit elasticity of 1 on every
route; the explicit alternatives (static, sensitivities, the marginal tax
rate convention); that a simulation without a reform, or without gains,
never measures a rate; that marginal tax rates hold realisations fixed; and
that the assumption a simulation applies can be read and recorded.
"""

import json
import math
import warnings

import numpy as np
import pandas as pd
import pytest

import policyengine_uk.utils.capital_gains as capital_gains
from policyengine_uk import Microsimulation, Simulation
from policyengine_uk.data.dataset_schema import UKSingleYearDataset
from policyengine_uk.model_api import Scenario
from policyengine_uk.utils.capital_gains import (
    CapitalGainsResponseWarning,
    capital_gains_response_assumption,
)

YEAR = 2026
RESPONSES = "gov.simulation.capital_gains_responses"
EQUALISED_RATES = {
    "gov.hmrc.cgt.basic_rate": {str(YEAR): 0.20},
    "gov.hmrc.cgt.higher_rate": {str(YEAR): 0.40},
    "gov.hmrc.cgt.additional_rate": {str(YEAR): 0.45},
}
# A rate rise from 24% to 45% on the marginal pound of gains.
CENTRAL_FACTOR = (1 - 0.45) / (1 - 0.24)


def single(earnings: float, gains: float, **extra) -> dict:
    person = {
        "age": {YEAR: 45},
        "employment_income": {YEAR: earnings},
        "capital_gains": {YEAR: gains},
        **{name: {YEAR: value} for name, value in extra.items()},
    }
    return {
        "people": {"person": person},
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {"household": {"members": ["person"]}},
    }


# £100,000 of earnings and £200,000 of gains: the marginal pound of gains is
# taxed at 24% now and at 45% with the rates equalised.
ADDITIONAL_RATE_GAINER = single(100_000, 200_000)
# £40,000 of earnings and £12,770 of gains: the gains end £500 below the top
# of the basic rate band, so a £1,000 pay rise moves the marginal pound of
# gains into the higher rate band.
BAND_EDGE_GAINER = single(40_000, 12_770)


def elasticities(**settings) -> dict:
    return {
        f"{RESPONSES}.{name}": {str(YEAR): value} for name, value in settings.items()
    }


def build(cls, situation, changes, route):
    if route == "reform":
        return cls(situation=situation, reform=changes)
    return cls(situation=situation, scenario=Scenario(parameter_changes=changes))


def values(sim, variable, period=YEAR) -> np.ndarray:
    result = sim.calculate(variable, period)
    return np.asarray(getattr(result, "values", result))


def realisation_factor(sim, person: int = 0, period=YEAR) -> float:
    gains = values(sim, "capital_gains_before_response", period)[person]
    response = values(sim, "capital_gains_behavioural_response", period)[person]
    return 1 + response / gains


@pytest.fixture
def measurements(monkeypatch):
    """Counts the capital gains marginal rates measured."""
    count = {"n": 0}
    measure = capital_gains.measure_mtr

    def counted(*args, **kwargs):
        count["n"] += 1
        return measure(*args, **kwargs)

    monkeypatch.setattr(capital_gains, "measure_mtr", counted)
    return count


# The default, on every route.


@pytest.mark.parametrize("cls", [Simulation, Microsimulation])
@pytest.mark.parametrize("route", ["reform", "scenario"])
def test_the_default_is_an_explicit_elasticity_of_one(cls, route):
    default = build(cls, ADDITIONAL_RATE_GAINER, EQUALISED_RATES, route)
    explicit = build(
        cls,
        ADDITIONAL_RATE_GAINER,
        {**EQUALISED_RATES, **elasticities(elasticity=1.0)},
        route,
    )

    assert realisation_factor(default) == pytest.approx(CENTRAL_FACTOR, abs=1e-5)
    for variable in ("capital_gains", "capital_gains_tax", "household_net_income"):
        assert list(values(default, variable)) == list(values(explicit, variable))


def dataset() -> UKSingleYearDataset:
    """A gainer at the additional rate, one with relief gains, a non-gainer
    and a net loss."""
    ids = np.arange(1, 5)
    return UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": ids,
                "person_benunit_id": ids,
                "person_household_id": ids,
                "age": [45, 50, 45, 45],
                "employment_income": [100_000.0, 200_000.0, 30_000.0, 150_000.0],
                "capital_gains_before_response": [
                    200_000.0,
                    500_000.0,
                    0.0,
                    -10_000.0,
                ],
                "capital_gains_badr": [0.0, 250_000.0, 0.0, 0.0],
            }
        ),
        benunit=pd.DataFrame({"benunit_id": ids}),
        household=pd.DataFrame(
            {
                "household_id": ids,
                "household_weight": [1.0, 1.0, 1.0, 1.0],
                "region": "LONDON",
                "tenure_type": "OWNED_OUTRIGHT",
                "rent": 0.0,
                "council_tax": 0.0,
            }
        ),
        fiscal_year=YEAR,
    )


def test_the_default_matches_on_a_dataset():
    default = Microsimulation(dataset=dataset(), reform=EQUALISED_RATES)
    explicit = Microsimulation(
        dataset=dataset(),
        reform={**EQUALISED_RATES, **elasticities(elasticity=1.0)},
    )

    for variable in ("capital_gains", "capital_gains_tax", "household_net_income"):
        assert list(values(default, variable)) == list(values(explicit, variable))
    response = values(default, "capital_gains_behavioural_response")
    assert response[0] < 0 and response[1] < 0
    # No gains, and a net loss, which pays no tax at the margin under either
    # set of rates.
    assert response[2] == 0 and response[3] == 0


def test_relief_gains_take_the_central_elasticity_by_default():
    sim = Simulation(
        situation=single(200_000, 500_000, capital_gains_badr=250_000),
        reform={
            **EQUALISED_RATES,
            "gov.hmrc.cgt.badr.lifetime_limit": {str(YEAR): 0},
        },
    )

    assert values(sim, "capital_gains_badr_elasticity")[0] == 1.0
    badr_gains = 250_000
    badr_response = values(sim, "capital_gains_badr_behavioural_response")[0]
    assert 1 + badr_response / badr_gains == pytest.approx(
        realisation_factor(sim), abs=1e-6
    )


def test_a_rate_cut_raises_realisations():
    cut = {
        "gov.hmrc.cgt.higher_rate": {str(YEAR): 0.18},
        "gov.hmrc.cgt.additional_rate": {str(YEAR): 0.18},
    }
    sim = Simulation(situation=ADDITIONAL_RATE_GAINER, reform=cut)

    assert realisation_factor(sim) == pytest.approx(0.82 / 0.76, abs=1e-5)


# Explicit alternatives.


@pytest.mark.parametrize("elasticity", [0.5, 1.3, 2.0])
def test_other_retention_rate_elasticities(elasticity):
    sim = Simulation(
        situation=ADDITIONAL_RATE_GAINER,
        reform={**EQUALISED_RATES, **elasticities(elasticity=elasticity)},
    )

    assert realisation_factor(sim) == pytest.approx(
        CENTRAL_FACTOR**elasticity, abs=1e-5
    )


def test_the_static_settings_give_no_response():
    sim = Simulation(
        situation=ADDITIONAL_RATE_GAINER,
        reform={
            **EQUALISED_RATES,
            **elasticities(
                elasticity=0, mtr_elasticity=0, separate_badr_elasticity=False
            ),
        },
    )

    assert values(sim, "capital_gains_behavioural_response")[0] == 0
    assert capital_gains_response_assumption(sim, YEAR).convention == "static"


# The marginal tax rate convention.


def collect(action):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = action()
    return result, [
        warning
        for warning in caught
        if issubclass(warning.category, CapitalGainsResponseWarning)
    ]


def test_an_mtr_elasticity_alone_applies_with_one_warning():
    """The retention-rate default counts as zero where an MTR elasticity is set
    alone, with a warning, given once however often the response is read."""
    legacy = Simulation(
        situation=ADDITIONAL_RATE_GAINER,
        reform={**EQUALISED_RATES, **elasticities(mtr_elasticity=-0.7)},
    )

    def read():
        legacy.calculate("household_net_income", YEAR)
        legacy.calculate("marginal_tax_rate", YEAR)
        legacy.delete_arrays("capital_gains_behavioural_response", YEAR)
        return realisation_factor(legacy)

    factor, caught = collect(read)

    # (45% / 24%) ** -0.7, not the retention-rate 0.55 / 0.76.
    assert factor == pytest.approx(math.exp(-0.7 * math.log(0.45 / 0.24)), abs=1e-5)
    assert len(caught) == 1
    assert "mtr_elasticity is -0.7 in 2026" in str(caught[0].message)

    explicit = Simulation(
        situation=ADDITIONAL_RATE_GAINER,
        reform={
            **EQUALISED_RATES,
            **elasticities(elasticity=0, mtr_elasticity=-0.7),
        },
    )
    explicit_factor, silent = collect(lambda: realisation_factor(explicit))
    assert explicit_factor == factor
    assert silent == []


def test_the_warning_comes_again_for_another_period():
    changes = {
        f"{RESPONSES}.mtr_elasticity": {"2026-01-01.2027-12-31": -0.5},
    }
    sim = Simulation(situation=ADDITIONAL_RATE_GAINER, reform=changes)

    _, first = collect(lambda: sim.calculate("capital_gains", 2026))
    _, again = collect(lambda: sim.calculate("capital_gains", 2026))
    _, second = collect(lambda: sim.calculate("capital_gains", 2027))
    assert (len(first), len(again), len(second)) == (1, 0, 1)


def test_conflicting_settings_raise_in_their_own_period():
    """An MTR elasticity over two years, with a retention-rate elasticity
    changed in the second only: the first resolves, the second raises."""
    sim = Simulation(
        situation=ADDITIONAL_RATE_GAINER,
        reform={
            f"{RESPONSES}.mtr_elasticity": {"2026-01-01.2027-12-31": -0.5},
            f"{RESPONSES}.elasticity": {"2027-01-01.2027-12-31": 0.5},
        },
    )

    collect(lambda: sim.calculate("capital_gains", 2026))
    with pytest.raises(ValueError, match=r"elasticity and .*mtr_elasticity"):
        sim.calculate("capital_gains", 2027)


def test_an_explicit_default_elasticity_resolves_like_an_inherited_one():
    """An elasticity set to its default value of 1 can't be told apart from
    the default, so alongside an MTR elasticity it resolves, with the warning,
    rather than raising."""
    sim = Simulation(
        situation=ADDITIONAL_RATE_GAINER,
        reform={
            **EQUALISED_RATES,
            **elasticities(elasticity=1.0, mtr_elasticity=-0.5),
        },
    )

    assumption, caught = collect(lambda: capital_gains_response_assumption(sim, YEAR))
    assert assumption.convention == "mtr"
    assert len(caught) == 1


# Dated settings.


def test_a_dated_elasticity_applies_only_in_its_year():
    sim = Simulation(
        situation=ADDITIONAL_RATE_GAINER,
        reform={f"{RESPONSES}.elasticity": {"2027-01-01.2027-12-31": 2.0}},
    )

    assert [
        capital_gains_response_assumption(sim, year).elasticity
        for year in (2026, 2027, 2028)
    ] == [1.0, 2.0, 1.0]
    assert values(sim, "capital_gains_elasticity", 2027)[0] == 2.0


# What is never measured.


def test_a_simulation_without_a_reform_never_measures(measurements):
    sim = Simulation(situation=BAND_EDGE_GAINER)
    for variable in (
        "household_net_income",
        "marginal_tax_rate",
        "marginal_tax_rate_wrt_employer_cost",
        "marginal_tax_rate_on_capital_gains",
    ):
        sim.calculate(variable, YEAR)

    assert measurements["n"] == 0
    assert values(sim, "capital_gains_behavioural_response")[0] == 0


def test_a_reforms_own_baseline_never_measures(measurements):
    sim = Simulation(situation=ADDITIONAL_RATE_GAINER, reform=EQUALISED_RATES)
    sim.calculate("household_net_income", YEAR)
    reform_measurements = measurements["n"]
    sim.baseline.calculate("household_net_income", YEAR)

    assert reform_measurements == 2
    assert measurements["n"] == reform_measurements
    assert values(sim.baseline, "capital_gains_behavioural_response")[0] == 0


def test_no_gains_means_no_measurement(measurements):
    sim = Simulation(situation=single(100_000, 0), reform=EQUALISED_RATES)
    sim.calculate("household_net_income", YEAR)

    assert measurements["n"] == 0


def test_a_loss_is_measured(measurements):
    """A loss counts as gains to respond: only the rates say it doesn't."""
    sim = Simulation(situation=single(150_000, -10_000), reform=EQUALISED_RATES)
    sim.calculate("household_net_income", YEAR)

    assert measurements["n"] == 2
    assert values(sim, "capital_gains_behavioural_response")[0] == 0


def test_a_change_to_the_elasticity_alone_gives_no_response():
    sim = Simulation(
        situation=ADDITIONAL_RATE_GAINER, reform=elasticities(elasticity=2.0)
    )

    assert values(sim, "capital_gains_behavioural_response")[0] == 0


def test_an_unreformed_simulation_matches_a_static_one():
    """Without a reform, every result is as if the response were off,
    marginal tax rates included."""
    default = Simulation(situation=BAND_EDGE_GAINER)
    static = Simulation(
        situation=BAND_EDGE_GAINER,
        reform={f"{RESPONSES}.elasticity": {"2000-01-01.2100-12-31": 0.0}},
    )

    for variable in (
        "capital_gains",
        "capital_gains_tax",
        "household_net_income",
        "marginal_tax_rate",
        "marginal_tax_rate_wrt_employer_cost",
        "marginal_tax_rate_on_capital_gains",
    ):
        assert list(values(default, variable)) == list(values(static, variable)), (
            variable
        )


# The marginal rate on gains.


def _readers(node, name: str, found: set) -> None:
    for child in node.children:
        if child.name == name:
            found.add(node.name)
        _readers(child, name, found)


def test_realised_gains_reach_net_income_only_as_income_and_through_the_tax():
    """marginal_tax_rate_on_capital_gains counts only the rise in capital
    gains tax. That is the share of marginal gains household net income does
    not keep only while gains reach net income as market income and through
    capital_gains_tax. This traces a net income calculation for a gainer with
    relief gains; if another variable starts reading capital_gains, the rate
    has to count it."""
    sim = Simulation(
        situation=single(200_000, 500_000, capital_gains_badr=250_000), trace=True
    )
    sim.calculate("household_net_income", YEAR)
    readers = set()
    for tree in sim.tracer.trees:
        _readers(tree, "capital_gains", readers)

    assert readers == {"household_market_income", "capital_gains_tax"}


@pytest.mark.parametrize(
    "earnings, gains",
    [(40_000, 12_770), (80_000, 50_000), (200_000, 500_000), (15_000, 20_000)],
    ids=["band-edge", "higher", "additional", "low-earner"],
)
def test_the_rate_on_gains_is_the_share_net_income_does_not_keep(earnings, gains):
    """Measured from capital gains tax, the rate equals one minus the rise in
    household net income per pound of marginal gains."""
    rate = values(
        Simulation(situation=single(earnings, gains)),
        "marginal_tax_rate_on_capital_gains",
    )[0]
    net = values(Simulation(situation=single(earnings, gains)), "household_net_income")[
        0
    ]
    higher = values(
        Simulation(situation=single(earnings, gains + 1_000)), "household_net_income"
    )[0]

    assert rate == pytest.approx(1 - (higher - net) / 1_000, abs=1e-4)


# Marginal tax rates hold realisations fixed.


def test_pay_rise_branches_hold_the_realisation_response():
    """A pay rise is not a reform for the response to answer.

    The marginal tax rate's pay-rise branch measured the reform's rate on
    gains at the higher pay against the baseline's at the old pay. At the
    band edge the extra £1,000 moves the gains into the higher rate band, so
    the branch counted the move as part of the reform: the response there
    was about eight times the reform's, and the marginal tax rate came out
    at over 800%. The branch now reads the reform's response, so the rate
    equals that of a simulation holding the realised gains fixed."""
    reform = Simulation(situation=BAND_EDGE_GAINER, reform=EQUALISED_RATES)
    realised = float(values(reform, "capital_gains")[0])
    static = Simulation(
        situation=single(40_000, realised),
        reform={**EQUALISED_RATES, **elasticities(elasticity=0)},
    )

    rate = values(reform, "marginal_tax_rate")[0]
    assert realised < 12_770
    assert rate == pytest.approx(values(static, "marginal_tax_rate")[0], abs=1e-6)
    assert 0 < rate < 1
    branch = reform.branches["adult_1_pay_rise"]
    assert list(values(branch, "capital_gains_behavioural_response")) == list(
        values(reform, "capital_gains_behavioural_response")
    )


def test_employer_cost_branches_hold_the_realisation_response():
    reform = Simulation(situation=BAND_EDGE_GAINER, reform=EQUALISED_RATES)
    realised = float(values(reform, "capital_gains")[0])
    static = Simulation(
        situation=single(40_000, realised),
        reform={**EQUALISED_RATES, **elasticities(elasticity=0)},
    )

    assert values(reform, "marginal_tax_rate_wrt_employer_cost")[0] == (
        pytest.approx(
            values(static, "marginal_tax_rate_wrt_employer_cost")[0], abs=1e-6
        )
    )


# Stability and isolation.


RESPONSE_PARTS = (
    "capital_gains_behavioural_response",
    "capital_gains_badr_behavioural_response",
    "relative_capital_gains_retention_rate_change",
)


def response_parts(sim) -> dict:
    return {variable: list(values(sim, variable)) for variable in RESPONSE_PARTS}


def test_the_default_response_is_stable_across_recalculation_and_order():
    sim = Simulation(situation=BAND_EDGE_GAINER, reform=EQUALISED_RATES)
    sim.calculate("household_net_income", YEAR)
    sim.calculate("marginal_tax_rate", YEAR)
    first = response_parts(sim)
    for variable in RESPONSE_PARTS:
        sim.delete_arrays(variable, YEAR)

    baseline_first = Simulation(situation=BAND_EDGE_GAINER, reform=EQUALISED_RATES)
    baseline_first.baseline.calculate("household_net_income", YEAR)
    baseline_first.baseline.calculate("marginal_tax_rate_on_capital_gains", YEAR)

    assert first["capital_gains_behavioural_response"][0] < 0
    assert response_parts(sim) == first
    assert response_parts(baseline_first) == first


def test_measuring_leaves_the_baseline_and_the_system_alone():
    sim = Simulation(situation=ADDITIONAL_RATE_GAINER, reform=EQUALISED_RATES)
    baseline = sim.baseline
    baseline_gains = list(values(baseline, "capital_gains"))
    response = sim.tax_benefit_system.variables["capital_gains_behavioural_response"]
    filters = list(warnings.filters)

    sim.calculate("household_net_income", YEAR)

    assert list(values(baseline, "capital_gains")) == baseline_gains
    assert sim.baseline is baseline
    assert (
        sim.tax_benefit_system.variables["capital_gains_behavioural_response"]
        is response
    )
    assert not response.is_neutralized
    assert not baseline.tax_benefit_system.variables[
        "capital_gains_behavioural_response"
    ].is_neutralized
    assert list(warnings.filters) == filters


def update_rates(sim) -> None:
    parameters = sim.tax_benefit_system.parameters
    for path, rates in EQUALISED_RATES.items():
        parameters.get_child(path).update(
            period=f"year:{YEAR}:1", value=rates[str(YEAR)]
        )
    sim.tax_benefit_system.reset_parameter_caches()


def test_rules_changed_after_construction_still_respond():
    """A simulation built without a reform and edited afterwards, as
    policyengine.py's modifiers do, responds against the rules it was built
    with."""
    sim = Simulation(situation=ADDITIONAL_RATE_GAINER)
    update_rates(sim)

    assert realisation_factor(sim) == pytest.approx(CENTRAL_FACTOR, abs=1e-5)


def test_a_modifier_that_registers_the_baseline_as_a_branch_still_responds():
    """uk-cgt-reform's modifier registers the baseline as a branch before
    editing the parameters."""
    sim = Simulation(situation=ADDITIONAL_RATE_GAINER)
    sim.branches["baseline"] = sim.baseline
    update_rates(sim)

    assert realisation_factor(sim) == pytest.approx(CENTRAL_FACTOR, abs=1e-5)


def test_parameter_changes_applied_after_construction_still_respond():
    sim = Simulation(situation=ADDITIONAL_RATE_GAINER)
    sim.apply_parameter_changes(EQUALISED_RATES)

    assert realisation_factor(sim) == pytest.approx(CENTRAL_FACTOR, abs=1e-5)


# The assumption a simulation applies.


def test_the_assumption_reports_the_default():
    sim = Simulation(situation=ADDITIONAL_RATE_GAINER, reform=EQUALISED_RATES)
    assumption = capital_gains_response_assumption(sim, YEAR)

    assert assumption.to_dict() == {
        "period": "2026",
        "convention": "retention",
        "elasticity": 1.0,
        "badr_elasticity": 1.0,
        "mtr_elasticity": 0.0,
        "separate_badr_elasticity": False,
        "sources": {
            "elasticity": "default",
            "badr_elasticity": "default",
            "mtr_elasticity": "default",
            "separate_badr_elasticity": "default",
        },
        "mtr_auto_resolved": False,
        "warnings": [],
    }
    assert json.loads(json.dumps(assumption.to_dict())) == assumption.to_dict()


def test_the_assumption_reports_overrides_and_the_obr_comparison():
    sim = Simulation(
        situation=ADDITIONAL_RATE_GAINER,
        reform=elasticities(elasticity=3.6, separate_badr_elasticity=True),
    )
    assumption = capital_gains_response_assumption(sim, YEAR)

    assert (assumption.elasticity, assumption.badr_elasticity) == (3.6, 1.4)
    assert assumption.sources == {
        "elasticity": "override",
        "badr_elasticity": "override",
        "mtr_elasticity": "default",
        "separate_badr_elasticity": "override",
    }


def test_the_assumption_reports_an_auto_resolved_mtr_elasticity():
    sim = Simulation(
        situation=ADDITIONAL_RATE_GAINER,
        reform=elasticities(mtr_elasticity=-0.7),
    )
    assumption, _ = collect(lambda: capital_gains_response_assumption(sim, YEAR))

    assert assumption.convention == "mtr"
    assert (assumption.elasticity, assumption.badr_elasticity) == (0.0, 0.0)
    assert assumption.mtr_auto_resolved
    assert assumption.sources["elasticity"] == "auto_resolved"
    assert len(assumption.warnings) == 1
