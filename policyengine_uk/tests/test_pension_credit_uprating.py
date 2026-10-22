"""Pension Credit's statutory earnings floor and linked projected amounts.

SSAA 1992 s150A(2) requires the standard minimum guarantee's annual increase
to be at least earnings growth. Projections use the published May-July AWE
figure, with no cut when earnings fall. The pension-age HB allowances follow
the same increase; the Savings Credit maximum follows September CPI, with
the threshold implied by the maximum and the 60% phase-in rate.
"""

from decimal import ROUND_HALF_UP, Decimal

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st
from policyengine_core.parameters import ParameterNode, load_parameter_file
from policyengine_core.parameters.operations.propagate_parameter_metadata import (
    propagate_parameter_metadata,
)
from policyengine_core.parameters.operations.uprate_parameters import uprate_parameters

from policyengine_uk.parameters.gov.economic_assumptions.create_earnings_uprating import (
    add_earnings_uprating,
)
from policyengine_uk.parameters.gov.economic_assumptions.create_economic_assumption_indices import (
    create_economic_assumption_indices,
)
from policyengine_uk.system import system
from policyengine_uk.tax_benefit_system import COUNTRY_DIR

EARNINGS_INDEX = "gov.economic_assumptions.indices.earnings_uprating"
FIRST_PROJECTION_YEAR = 2027
LAST_INDEX_YEAR = 2039
SMG_NAME = "gov.dwp.pension_credit.guarantee_credit.minimum_guarantee"
HB_NAME = "gov.dwp.housing_benefit.allowances"
RAW_SMG = load_parameter_file(
    str(
        COUNTRY_DIR
        / "parameters/gov/dwp/pension_credit/guarantee_credit/minimum_guarantee.yaml"
    ),
    name=SMG_NAME,
)
RAW_HB = load_parameter_file(
    str(COUNTRY_DIR / "parameters/gov/dwp/housing_benefit/allowances"), name=HB_NAME
)

# Includes negative earnings, off-grid forecasts and different CPI paths.
growth = st.integers(min_value=-600, max_value=1500).map(lambda n: n / 10_000)
paths = st.lists(st.tuples(growth, growth), min_size=1, max_size=10)


def published_earnings_floor(rate):
    """Independent transcription of the published 0.1pp earnings figure."""
    rounded = Decimal(str(rate)).quantize(Decimal("0.001"), ROUND_HALF_UP)
    return max(float(rounded), 0.0)


def synthetic_parameters(path):
    """Uprate the production SMG and six HB leaves without a simulation.

    Earlier observations merely supply the index's 2010 base; every generated
    path begins with the May-July figure for the first projected April.
    """
    observations = {year: (0.02, 0.02) for year in range(2010, 2026)}
    observations.update({2026 + i: values for i, values in enumerate(path)})
    parameters = ParameterNode(
        data={
            "gov": {
                "economic_assumptions": {
                    "statutory_uprating_inputs": {
                        "awe_total_pay_may_july": {
                            "values": {
                                f"{year}-07-01": earnings
                                for year, (earnings, _) in observations.items()
                            }
                        },
                        "cpi_september": {
                            "values": {
                                f"{year}-09-01": cpi
                                for year, (_, cpi) in observations.items()
                            }
                        },
                    },
                    "yoy_growth": {
                        "obr": {
                            name: {
                                "values": {
                                    f"{year}-01-01": values[position]
                                    for year, values in observations.items()
                                }
                            }
                            for name, position in (
                                ("average_earnings", 0),
                                ("consumer_price_index", 1),
                            )
                        }
                    },
                },
                "dwp": {
                    "pension_credit": {"guarantee_credit": {}},
                    "housing_benefit": {"allowances": {}},
                },
            }
        }
    )
    parameters.gov.dwp.pension_credit.guarantee_credit.add_child(
        "minimum_guarantee", RAW_SMG.clone()
    )
    # Only pension-age amounts belong to the earnings link. Including the
    # working-age leaves would need the unrelated CPI index too.
    allowances = parameters.gov.dwp.housing_benefit.allowances
    for kind in ("single", "couple", "lone_parent"):
        node = ParameterNode(name=f"{HB_NAME}.{kind}", data={})
        for cohort in ("aged", "aged_from_cutoff"):
            node.add_child(cohort, getattr(getattr(RAW_HB, kind), cohort).clone())
        allowances.add_child(kind, node)
    parameters = create_economic_assumption_indices(add_earnings_uprating(parameters))
    propagate_parameter_metadata(parameters)
    uprate_parameters(parameters)
    return parameters


def earnings_linked_amounts(parameters):
    minimum = parameters.gov.dwp.pension_credit.guarantee_credit.minimum_guarantee
    yield minimum.SINGLE
    yield minimum.COUPLE
    allowances = parameters.gov.dwp.housing_benefit.allowances
    for kind in ("single", "couple", "lone_parent"):
        node = getattr(allowances, kind)
        yield node.aged
        yield node.aged_from_cutoff


@settings(max_examples=60, deadline=None)
@given(path=paths)
@example(path=[(0.01, 0.10), (-0.02, 0.05), (0.08, -0.01)])
def test_projected_smg_and_hb_never_rise_by_less_than_published_earnings(path):
    """Check amounts, not just the rate helper, under diverging inputs.

    CPI cannot replace the earnings floor or add the State Pension's price
    protection. Falling earnings hold these amounts rather than cutting them.
    """
    parameters = synthetic_parameters(path)
    for parameter in earnings_linked_amounts(parameters):
        assert parameter.metadata["uprating"] == EARNINGS_INDEX
        for i, (earnings, _) in enumerate(path):
            year = FIRST_PROJECTION_YEAR + i
            before = parameter(f"{year - 1}-04-30")
            after = parameter(f"{year}-04-30")
            floor = published_earnings_floor(earnings)
            assert after >= before * (1 + floor) - 1e-10, (parameter.name, year)
            assert after / before - 1 == pytest.approx(floor, abs=1e-12)


def test_baseline_smg_and_hb_respect_the_earnings_floor_in_every_projected_year():
    parameters = system.parameters
    awe = parameters.gov.economic_assumptions.statutory_uprating_inputs.awe_total_pay_may_july
    for parameter in earnings_linked_amounts(parameters):
        for year in range(FIRST_PROJECTION_YEAR, LAST_INDEX_YEAR + 1):
            before = parameter(f"{year - 1}-04-30")
            after = parameter(f"{year}-04-30")
            floor = published_earnings_floor(awe(f"{year - 1}-07-01"))
            assert after >= before * (1 + floor) - 1e-10, (parameter.name, year)
            assert after / before - 1 == pytest.approx(floor, abs=1e-12)


@pytest.mark.parametrize("relation", ["SINGLE", "COUPLE"])
def test_savings_credit_threshold_preserves_the_cpi_uprated_maximum(relation):
    parameters = system.parameters
    pc = parameters.gov.dwp.pension_credit
    minimum = getattr(pc.guarantee_credit.minimum_guarantee, relation)
    threshold = getattr(pc.savings_credit.threshold, relation)
    maximum = getattr(pc.savings_credit.maximum, relation)
    phase_in = pc.savings_credit.rate.phase_in
    cpi = parameters.gov.economic_assumptions.yoy_growth.september_cpi_uprating
    for year in range(FIRST_PROJECTION_YEAR, LAST_INDEX_YEAR + 1):
        at = f"{year}-04-30"
        before = f"{year - 1}-04-30"
        assert phase_in(at) * (minimum(at) - threshold(at)) == pytest.approx(
            maximum(at), abs=1e-10
        )
        # CPI indices retain their existing five-decimal-place rounding.
        assert maximum(at) / maximum(before) - 1 == pytest.approx(
            cpi(f"{year}-01-01"), abs=2e-5
        )


def test_hb_lower_pension_age_allowances_stay_equal_to_the_standard_minimum_guarantee():
    parameters = system.parameters.gov.dwp
    minimum = parameters.pension_credit.guarantee_credit.minimum_guarantee
    allowances = parameters.housing_benefit.allowances
    for year in range(2021, LAST_INDEX_YEAR + 1):
        at = f"{year}-04-30"
        assert allowances.single.aged_from_cutoff(at) == minimum.SINGLE(at)
        assert allowances.lone_parent.aged_from_cutoff(at) == minimum.SINGLE(at)
        assert allowances.couple.aged_from_cutoff(at) == minimum.COUPLE(at)
