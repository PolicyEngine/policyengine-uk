"""Pension Credit's statutory earnings floor and linked projected amounts.

SSAA 1992 s150A(2) requires the standard minimum guarantee's annual increase
to be at least earnings growth. Projections use the published May-July AWE
figure, with no cut when earnings fall. The lower pension-age HB allowances
equal the guarantee and follow the same increase. The Savings Credit maximum
follows September CPI, with the threshold implied by the maximum and the
60% phase-in rate. The higher pension-age HB allowances are the guarantee
plus that maximum (HB A3/2021), so each part keeps its own index.

Invariants, for every earnings, CPI and phase-in path:

1. The guarantee and lower HB allowances rise by exactly the published
   earnings figure, and never fall.
2. Each higher HB allowance equals the projected guarantee plus the
   projected Savings Credit maximum, after its published amounts.
3. A positive phase-in rate times the guarantee less the threshold is the
   maximum; a zero rate keeps the threshold in force before it.
4. Published amounts are unchanged by the projections.
"""

from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import pytest
import yaml
from hypothesis import example, given, settings
from hypothesis import strategies as st
from policyengine_core.parameters import ParameterNode, load_parameter_file
from policyengine_core.parameters.operations.propagate_parameter_metadata import (
    propagate_parameter_metadata,
)
from policyengine_core.parameters.operations.uprate_parameters import uprate_parameters

from policyengine_uk import Simulation
from policyengine_uk.parameters.gov.dwp.housing_benefit.allowances.create_pension_age_allowances import (
    project_pension_age_allowances,
)
from policyengine_uk.parameters.gov.dwp.pension_credit.savings_credit.create_savings_credit_threshold import (
    project_savings_credit_threshold,
)
from policyengine_uk.parameters.gov.economic_assumptions.create_earnings_uprating import (
    add_earnings_uprating,
)
from policyengine_uk.parameters.gov.economic_assumptions.create_economic_assumption_indices import (
    create_economic_assumption_indices,
)
from policyengine_uk.parameters.gov.economic_assumptions.create_september_cpi_uprating import (
    add_september_cpi_uprating,
)
from policyengine_uk.system import system
from policyengine_uk.tax_benefit_system import COUNTRY_DIR

EARNINGS_INDEX = "gov.economic_assumptions.indices.earnings_uprating"
FIRST_PROJECTION_YEAR = 2027
LAST_INDEX_YEAR = 2039
LAST_PUBLISHED_YEAR = FIRST_PROJECTION_YEAR - 1
PARAMETERS_DIR = COUNTRY_DIR / "parameters"
SMG_NAME = "gov.dwp.pension_credit.guarantee_credit.minimum_guarantee"
SC_NAME = "gov.dwp.pension_credit.savings_credit"
HB_NAME = "gov.dwp.housing_benefit.allowances"
RAW_SMG = load_parameter_file(
    str(
        PARAMETERS_DIR
        / "gov/dwp/pension_credit/guarantee_credit/minimum_guarantee.yaml"
    ),
    name=SMG_NAME,
)
RAW_SC = load_parameter_file(
    str(PARAMETERS_DIR / "gov/dwp/pension_credit/savings_credit"), name=SC_NAME
)
RAW_HB = load_parameter_file(
    str(PARAMETERS_DIR / "gov/dwp/housing_benefit/allowances"), name=HB_NAME
)
RAW_BENEFIT_CPI = load_parameter_file(
    str(PARAMETERS_DIR / "gov/benefit_uprating_cpi.yaml"),
    name="gov.benefit_uprating_cpi",
)
# Each higher allowance's Pension Credit relation: a lone parent's is single.
HB_RELATIONS = {"single": "SINGLE", "couple": "COUPLE", "lone_parent": "SINGLE"}
PUBLISHED = yaml.safe_load(
    (
        Path(__file__).parent / "fixtures" / "dwp_benefit_and_pension_rates.yaml"
    ).read_text()
)["parameters"]

# Includes negative earnings, off-grid forecasts and different CPI paths.
growth = st.integers(min_value=-600, max_value=1500).map(lambda n: n / 10_000)
paths = st.lists(st.tuples(growth, growth), min_size=1, max_size=10)
# Zero, the 60% in force and rates either side of it, for each projected year.
phase_in_rates = st.one_of(st.just(0.0), st.integers(1, 100).map(lambda n: n / 100))
phase_in_paths = st.lists(phase_in_rates, min_size=1, max_size=10)


def published_rise(rate):
    """Independent transcription of a published 0.1pp figure, never a cut."""
    rounded = Decimal(str(rate)).quantize(Decimal("0.001"), ROUND_HALF_UP)
    return max(float(rounded), 0.0)


def add_node(parent, key):
    """Add an empty node; Core reads an empty dict as a parameter instead."""
    node = ParameterNode(name=f"{parent.name}.{key}", data={})
    parent.add_child(key, node)
    return node


def synthetic_parameters(path, phase_ins=()):
    """Uprate and project the production Pension Credit and HB amounts.

    No simulation is built. Earlier observations merely supply the indices'
    2010 base; every generated path begins with the May-July and September
    figures for the first projected April. ``phase_ins`` gives the Savings
    Credit phase-in rate from each projected April, in order.
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
            }
        }
    )
    parameters.gov.add_child("benefit_uprating_cpi", RAW_BENEFIT_CPI.clone())
    dwp = add_node(parameters.gov, "dwp")
    pension_credit = add_node(dwp, "pension_credit")
    guarantee_credit = add_node(pension_credit, "guarantee_credit")
    guarantee_credit.add_child("minimum_guarantee", RAW_SMG.clone())
    savings_credit = RAW_SC.clone()
    phase_in = savings_credit.rate.phase_in
    for i, rate in enumerate(phase_ins):
        phase_in.update(start=f"{FIRST_PROJECTION_YEAR + i}-01-01", value=rate)
    pension_credit.add_child("savings_credit", savings_credit)
    # Only pension-age amounts belong to the earnings link. Including the
    # working-age leaves would need the unrelated CPI index too.
    allowances = add_node(add_node(dwp, "housing_benefit"), "allowances")
    for kind in HB_RELATIONS:
        node = add_node(allowances, kind)
        for cohort in ("aged", "aged_from_cutoff"):
            node.add_child(cohort, getattr(getattr(RAW_HB, kind), cohort).clone())
    parameters = add_september_cpi_uprating(add_earnings_uprating(parameters))
    parameters = create_economic_assumption_indices(parameters)
    propagate_parameter_metadata(parameters)
    uprate_parameters(parameters)
    project_savings_credit_threshold(parameters)
    project_pension_age_allowances(parameters)
    return parameters


def earnings_linked_amounts(parameters):
    minimum = parameters.gov.dwp.pension_credit.guarantee_credit.minimum_guarantee
    yield minimum.SINGLE
    yield minimum.COUPLE
    allowances = parameters.gov.dwp.housing_benefit.allowances
    for kind in HB_RELATIONS:
        yield getattr(allowances, kind).aged_from_cutoff


def higher_allowances(parameters):
    """Each higher HB allowance with the guarantee and maximum it is built from."""
    pc = parameters.gov.dwp.pension_credit
    allowances = parameters.gov.dwp.housing_benefit.allowances
    for kind, relation in HB_RELATIONS.items():
        yield (
            getattr(allowances, kind).aged,
            getattr(pc.guarantee_credit.minimum_guarantee, relation),
            getattr(pc.savings_credit.maximum, relation),
        )


def assert_published_amounts_kept(parameters):
    """Invariant 4: the YAML's stated values, read where they are stated."""
    for raw, node in (
        (RAW_SMG, parameters.gov.dwp.pension_credit.guarantee_credit.minimum_guarantee),
        (RAW_SC.threshold, parameters.gov.dwp.pension_credit.savings_credit.threshold),
        (RAW_SC.maximum, parameters.gov.dwp.pension_credit.savings_credit.maximum),
    ):
        for relation in ("SINGLE", "COUPLE"):
            for entry in getattr(raw, relation).values_list:
                assert getattr(node, relation)(entry.instant_str) == entry.value
    allowances = parameters.gov.dwp.housing_benefit.allowances
    for kind in HB_RELATIONS:
        for cohort in ("aged", "aged_from_cutoff"):
            projected = getattr(getattr(allowances, kind), cohort)
            for entry in getattr(getattr(RAW_HB, kind), cohort).values_list:
                assert projected(entry.instant_str) == entry.value


@settings(max_examples=60, deadline=None)
@given(path=paths)
@example(path=[(0.01, 0.10), (-0.02, 0.05), (0.08, -0.01)])
def test_projected_smg_and_hb_never_rise_by_less_than_published_earnings(path):
    """Invariant 1, on amounts, not just the rate helper, under diverging inputs.

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
            floor = published_rise(earnings)
            assert after >= before * (1 + floor) - 1e-10, (parameter.name, year)
            assert after / before - 1 == pytest.approx(floor, abs=1e-12)


@settings(max_examples=60, deadline=None)
@given(path=paths)
@example(path=[(0.039, 0.035)])
@example(path=[(0.10, -0.02), (-0.03, 0.12), (0.0, 0.0)])
def test_higher_hb_allowances_keep_each_part_on_its_own_index(path):
    """Invariants 2 and 4: earnings move the guarantee part, CPI the maximum.

    Projecting the whole allowance by either index would misstate it once
    earnings and CPI diverge.
    """
    parameters = synthetic_parameters(path)
    assert_published_amounts_kept(parameters)
    for allowance, guarantee, maximum in higher_allowances(parameters):
        assert "uprating" not in allowance.metadata
        for i, (earnings, cpi) in enumerate(path):
            year = FIRST_PROJECTION_YEAR + i
            at, before = f"{year}-04-30", f"{year - 1}-04-30"
            assert allowance(at) == pytest.approx(
                guarantee(at) + maximum(at), abs=1e-9
            ), (allowance.name, year)
            assert guarantee(at) / guarantee(before) - 1 == pytest.approx(
                published_rise(earnings), abs=1e-12
            )
            # CPI indices keep five-decimal-place levels.
            assert maximum(at) / maximum(before) - 1 == pytest.approx(
                published_rise(cpi), abs=2e-5
            )


@settings(max_examples=60, deadline=None)
@given(path=paths, phase_ins=phase_in_paths)
@example(path=[(0.039, 0.035)], phase_ins=[0.0])
@example(path=[(0.039, 0.035), (0.02, 0.03), (0.05, 0.01)], phase_ins=[0.0, 0.6, 0.0])
def test_projected_threshold_keeps_the_maximum_at_every_phase_in_rate(path, phase_ins):
    """Invariant 3: a zero rate never divides, and keeps the threshold."""
    parameters = synthetic_parameters(path, phase_ins)
    assert_published_amounts_kept(parameters)
    pc = parameters.gov.dwp.pension_credit
    phase_in = pc.savings_credit.rate.phase_in
    for relation in ("SINGLE", "COUPLE"):
        guarantee = getattr(pc.guarantee_credit.minimum_guarantee, relation)
        threshold = getattr(pc.savings_credit.threshold, relation)
        maximum = getattr(pc.savings_credit.maximum, relation)
        for year in range(FIRST_PROJECTION_YEAR, LAST_INDEX_YEAR + 1):
            at, before = f"{year}-04-30", f"{year - 1}-04-30"
            rate = phase_in(at)
            if rate == 0:
                assert threshold(at) == threshold(before), (relation, year)
            else:
                assert rate * (guarantee(at) - threshold(at)) == pytest.approx(
                    maximum(at), abs=1e-9
                ), (relation, year, rate)


def test_baseline_smg_and_hb_respect_the_earnings_floor_in_every_projected_year():
    parameters = system.parameters
    awe = parameters.gov.economic_assumptions.statutory_uprating_inputs.awe_total_pay_may_july
    for parameter in earnings_linked_amounts(parameters):
        for year in range(FIRST_PROJECTION_YEAR, LAST_INDEX_YEAR + 1):
            before = parameter(f"{year - 1}-04-30")
            after = parameter(f"{year}-04-30")
            floor = published_rise(awe(f"{year - 1}-07-01"))
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


@pytest.mark.parametrize("year", range(2019, LAST_PUBLISHED_YEAR + 1))
@pytest.mark.parametrize("kind", sorted(HB_RELATIONS))
def test_published_higher_hb_allowances_are_the_guarantee_plus_the_savings_credit_maximum(
    kind, year
):
    """The premise of invariant 2, in DWP's published rates.

    The maximum is 60% of the guarantee less the threshold (State Pension
    Credit Regulations 2002 reg 7). Each published allowance is the
    guarantee plus that maximum, rounded up to the next 5p.
    """
    relation = HB_RELATIONS[kind]

    def published(name):
        return Decimal(str(PUBLISHED[name]["values"][year]))

    guarantee = published(f"{SMG_NAME}.{relation}")
    threshold = published(f"{SC_NAME}.threshold.{relation}")
    allowance = published(f"{HB_NAME}.{kind}.aged")
    maximum = Decimal("0.6") * (guarantee - threshold)
    assert Decimal(0) <= allowance - (guarantee + maximum) < Decimal("0.05")


def test_baseline_higher_hb_allowances_are_the_projected_guarantee_plus_maximum():
    """Invariants 2 and 4 in current law, against the indices directly.

    The differential side compounds each part's published amount by its own
    index, without reading the uprated guarantee or maximum.
    """
    parameters = system.parameters
    assert_published_amounts_kept(parameters)
    earnings = parameters.gov.economic_assumptions.indices.earnings_uprating
    benefit_cpi = parameters.gov.benefit_uprating_cpi
    last = f"{LAST_PUBLISHED_YEAR}-04-30"
    for allowance, guarantee, maximum in higher_allowances(parameters):
        for year in range(FIRST_PROJECTION_YEAR, LAST_INDEX_YEAR + 1):
            at = f"{year}-04-30"
            assert allowance(at) == pytest.approx(
                guarantee(at) + maximum(at), abs=1e-9
            ), (allowance.name, year)
            from_indices = guarantee(last) * earnings(at) / earnings(last) + maximum(
                last
            ) * benefit_cpi(at) / benefit_cpi(last)
            assert allowance(at) == pytest.approx(from_indices, abs=1e-9)


def zero_phase_in_situation():
    """A single pensioner with income between the threshold and the guarantee."""
    years = ("2027", "2028")
    return {
        "people": {"claimant": {"age": {"2027": 81, "2028": 82}}},
        "benunits": {
            "benunit": {
                "members": ["claimant"],
                "savings_credit_income": {year: 12_000 for year in years},
                "pension_credit_income": {year: 12_000 for year in years},
            }
        },
        "households": {"household": {"members": ["claimant"]}},
    }


def test_zero_phase_in_reform_builds_and_pays_no_savings_credit():
    """A zero Savings Credit phase-in rate for 2027-28 once divided by zero.

    It now keeps the 2026-27 threshold for that year, pays no Savings Credit,
    and leaves 2028-29 as current law has it.
    """
    reform = {"gov.dwp.pension_credit.savings_credit.rate.phase_in": {"2027": 0}}
    baseline = Simulation(situation=zero_phase_in_situation())
    reformed = Simulation(situation=zero_phase_in_situation(), reform=reform)
    # 0.6 * (12,000 - 216.301 * 52), as savings_credit.yaml computes.
    assert baseline.calculate("savings_credit", 2027)[0] == pytest.approx(
        451.4088, abs=0.01
    )
    assert reformed.calculate("savings_credit", 2027)[0] == 0
    assert reformed.calculate("savings_credit", 2028)[0] == pytest.approx(
        baseline.calculate("savings_credit", 2028)[0], abs=1e-6
    )
    assert reformed.calculate("guarantee_credit", 2027)[0] == pytest.approx(
        baseline.calculate("guarantee_credit", 2027)[0], abs=1e-6
    )
    threshold = reformed.tax_benefit_system.parameters.gov.dwp.pension_credit.savings_credit.threshold.SINGLE
    current = baseline.tax_benefit_system.parameters.gov.dwp.pension_credit.savings_credit.threshold.SINGLE
    assert threshold("2027-04-30") == pytest.approx(208.07)
    assert threshold("2028-04-30") == pytest.approx(current("2028-04-30"))


def test_reforms_keep_their_own_allowance_and_move_the_derived_one():
    """A dated change to a higher allowance is kept, and prior law resumes.

    A change to the guarantee moves the allowance derived from it in that
    year, as it moves the Savings Credit threshold; the lower allowance has
    its own earnings projection and does not follow.
    """
    reform = {
        f"{HB_NAME}.single.aged": {"2028": 300},
        f"{SMG_NAME}.COUPLE": {"2029": 400},
    }
    situation = {
        "people": {"claimant": {"age": {"2028": 81}}},
        "households": {"household": {"members": ["claimant"]}},
    }
    current = system.parameters
    reformed = Simulation(situation=situation, reform=reform).tax_benefit_system
    allowances = reformed.parameters.gov.dwp.housing_benefit.allowances
    now = current.gov.dwp.housing_benefit.allowances
    sc_max = reformed.parameters.gov.dwp.pension_credit.savings_credit.maximum
    for year in (2027, 2029, 2030):
        at = f"{year}-04-30"
        assert allowances.single.aged(at) == pytest.approx(now.single.aged(at))
    assert allowances.single.aged("2028-04-30") == 300
    assert allowances.couple.aged("2029-04-30") == pytest.approx(
        400 + sc_max.COUPLE("2029-04-30")
    )
    for year in (2028, 2030):
        at = f"{year}-04-30"
        assert allowances.couple.aged(at) == pytest.approx(now.couple.aged(at))
    assert allowances.couple.aged_from_cutoff("2029-04-30") == pytest.approx(
        now.couple.aged_from_cutoff("2029-04-30")
    )
