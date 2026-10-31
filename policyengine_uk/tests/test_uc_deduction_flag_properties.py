"""A supplied UC latent deduction rate follows the deduction flag (#2739).

uc_latent_deduction_rate's formula returns zero where uc_has_deduction is
false. uc_deduction_rate applies the same rule to a rate that a dataset or
situation supplies, and so does the advance estimate built from that rate.
uc_has_deduction reads the award the benefit cap leaves; a protected floor
reform limits the cap to the floor allowance (uc_maximum_reduction, infinite
under current law). ``MAIN_RULE`` re-adds origin/main's flag, rate and
advance formulas at 7ed52038a, verbatim, so one dataset gives both rules.

Invariants, each over generated benefit units and explicit examples:

1. Flag gate. Where uc_has_deduction is false, uc_deductions is zero, for
   any supplied latent rate, combination, benefit cap reduction and floor.
   The documented exception: an explicitly supplied
   uc_advance_repayment_amount describes a known advance and applies
   whatever the flag says.
2. Substitution. A supplied latent rate gives the same deductions, applied
   cap reduction and award as where(uc_has_deduction, rate, 0), the rate
   the formula's rule leaves.
3. The flag only gates disagreeing rates. For a claimant whose incidence
   draw assigns deductions, uc_deductions equals allocate_uc_reductions on
   the ungated demand, under any floor: the flag is false only where the
   allocation gives nothing.
4. Accounting. For a claimant with an award, uc_deductions plus
   uc_benefit_cap_reduction_after_floor plus universal_credit equals the
   award before the cap.
5. Current law. With no floor, a dataset without stored attributes (the
   formula path) gives the same flag, rates, deductions, applied cap and
   award as origin/main's rule, bit for bit.
6. Floor. Under a floor, the formula path moves only the split between
   deductions and the applied cap for families the cap takes to nil; their
   award rises by less than the 12p a year the penny rule keeps.
7. Stored attributes. A dataset that stores the draws and, for every unit
   the draw assigns (claimant or not), the formula's latent rate and
   combination, as Microcosm does, gives the formula path's flag,
   deductions, applied cap and award under any floor.
"""

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st
from policyengine_core.reforms import Reform

from policyengine_uk import Microsimulation, Simulation
from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.universal_credit.deductions._deduction_amounts import (
    deduction_type_shares,
    reference_standard_allowance,
)
from policyengine_uk.variables.gov.dwp.universal_credit.deductions._reduction_allocation import (
    allocate_uc_reductions,
)

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2025
# Single claimant 25 or over, 2025-26: £400.14 a month.
STANDARD_ALLOWANCE = 400.14 * 12
PENNY_A_YEAR = 0.01 * 12
COMBINATIONS = [
    "NONE",
    "ADVANCE_ONLY",
    "THIRD_PARTY_ONLY",
    "GOVERNMENT_ONLY",
    "ADVANCE_AND_GOVERNMENT",
    "ADVANCE_AND_THIRD_PARTY",
    "THIRD_PARTY_AND_GOVERNMENT",
    "ALL_THREE",
]
REGIONS = ["LONDON", "NORTH_EAST", "SCOTLAND", "WALES", "SOUTH_EAST"]
# Households in situations live in London by default, whose incidence is
# 0.467 x 0.94 = 0.439: a draw below 0.4 assigns deductions, one above 0.45
# does not.
ASSIGNING_DRAW = st.floats(0, 0.4, allow_nan=False)
NON_ASSIGNING_DRAW = st.floats(0.45, 1, exclude_max=True, allow_nan=False)
DEDUCTION_OUTPUTS = (
    "uc_deductions",
    "uc_benefit_cap_reduction_after_floor",
    "universal_credit",
)


def floor_reform(floor):
    if not floor:
        return None
    return {
        "gov.dwp.universal_credit.deductions.protected_floor": {
            f"{YEAR}-01-01.{YEAR}-12-31": floor
        }
    }


def values(sim, variable):
    return np.asarray(sim.calculate(variable, YEAR))


# Situations: each generated unit is a single claimant aged 30 in its own
# household, with its award and gross cap reduction supplied. A population
# either supplies every unit's flag or every unit's incidence draw: core
# fills the units a partly supplied input leaves out with its default, so a
# flag supplied for one unit would set the others' to false.

cash = st.integers(0, 2_000_000).map(lambda pennies: pennies / 100)
unit_strategy = st.fixed_dictionaries(
    {
        "pre_cap": cash,
        "gross_cap": st.integers(0, 2_500_000).map(lambda pennies: pennies / 100),
        "latent": st.floats(0, 0.4, allow_nan=False),
        "combination": st.sampled_from(COMBINATIONS),
        "flag": st.booleans(),
        "draw": st.one_of(ASSIGNING_DRAW, NON_ASSIGNING_DRAW),
        "claims": st.booleans(),
        "advance": st.one_of(st.none(), cash.map(lambda amount: amount / 10)),
    }
)
floor_strategy = st.one_of(st.just(0.0), st.floats(0.5, 1.2, allow_nan=False))


def situation(units, drawn, latent=None, flag=None):
    """A situation of ``units`` that supplies each unit's incidence draw if
    ``drawn`` and its flag otherwise. ``latent`` replaces every unit's latent
    rate; ``flag`` supplies every unit's flag."""
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        person = f"person_{i}"
        people[person] = {"age": {YEAR: 30}}
        benunit = {
            "members": [person],
            "would_claim_uc": {YEAR: unit["claims"]},
            "universal_credit_pre_benefit_cap": {YEAR: unit["pre_cap"]},
            "uc_benefit_cap_reduction": {YEAR: unit["gross_cap"]},
            "uc_latent_deduction_rate": {
                YEAR: unit["latent"] if latent is None else float(latent[i])
            },
            "uc_deduction_combination": {YEAR: unit["combination"]},
        }
        if flag is not None:
            benunit["uc_has_deduction"] = {YEAR: flag}
        elif drawn:
            benunit["uc_deduction_random_draw"] = {YEAR: unit["draw"]}
        else:
            benunit["uc_has_deduction"] = {YEAR: unit["flag"]}
        if unit["advance"] is not None:
            benunit["uc_advance_repayment_amount"] = {YEAR: unit["advance"]}
        benunits[f"benunit_{i}"] = benunit
        households[f"household_{i}"] = {"members": [person]}
    return {"people": people, "benunits": benunits, "households": households}


def family(**overrides):
    return {
        "pre_cap": 6_000.0,
        "gross_cap": 0.0,
        "latent": 0.25,
        "combination": "ADVANCE_ONLY",
        "flag": False,
        "draw": 0.9,
        "claims": True,
        "advance": None,
        **overrides,
    }


# The example from #2739: the cap takes the whole award, the flag is false,
# and a supplied rate of 30% gave £720.25 under an 85% floor.
ISSUE_EXAMPLE = family(pre_cap=1_000.0, gross_cap=1_000.0, latent=0.30, draw=0.1)
EXAMPLE_UNITS = [
    ISSUE_EXAMPLE,
    # Supplied flags: the issue's family flagged by hand, known advance cash
    # without the flag (the documented exception), and a non-claimant
    # flagged by hand. Drawn: the issue's family, which a floor leaves an
    # award, and a rate whose draw assigns nothing.
    family(pre_cap=1_000.0, gross_cap=1_000.0, latent=0.30, flag=True),
    family(advance=360.0),
    family(latent=0.30, combination="GOVERNMENT_ONLY", flag=True, claims=False),
    family(combination="ALL_THREE"),
]


@settings(
    max_examples=8,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    units=st.lists(unit_strategy, min_size=1, max_size=5),
    drawn=st.booleans(),
    floor=floor_strategy,
)
@example(units=EXAMPLE_UNITS, drawn=False, floor=0.85)
@example(units=EXAMPLE_UNITS, drawn=True, floor=0.85)
@example(units=EXAMPLE_UNITS, drawn=False, floor=0.0)
@example(units=EXAMPLE_UNITS, drawn=True, floor=0.0)
def test_the_flag_gates_a_supplied_latent_rate(units, drawn, floor):
    reform = floor_reform(floor)
    sim = Simulation(situation=situation(units, drawn), reform=reform)
    flag = values(sim, "uc_has_deduction").astype(bool)
    deductions = values(sim, "uc_deductions")
    supplied_advance = np.array([unit["advance"] is not None for unit in units])
    claims = values(sim, "claims_universal_credit").astype(bool)
    pre_cap = values(sim, "universal_credit_pre_benefit_cap")

    # 1. No deductions without the flag, unless known advance cash applies.
    assert np.all(deductions[~flag & ~supplied_advance] == 0)

    # 2. A supplied rate gives what the rate the flag leaves gives.
    latent = np.array([unit["latent"] for unit in units])
    substituted = Simulation(
        situation=situation(units, drawn, latent=np.where(flag, latent, 0)),
        reform=reform,
    )
    np.testing.assert_array_equal(values(substituted, "uc_has_deduction"), flag)
    for variable in DEDUCTION_OUTPUTS:
        np.testing.assert_allclose(
            values(sim, variable), values(substituted, variable), rtol=0, atol=1e-6
        )

    # 3. For a claimant the draw assigns, the flag removes nothing that the
    # allocation of its ungated demand would give.
    if drawn:
        ungated = Simulation(
            situation=situation(units, drawn, flag=True), reform=reform
        )
        demand = values(ungated, "uc_deduction_rate") * values(
            ungated, "uc_standard_allowance"
        )
        expected, _ = allocate_uc_reductions(
            pre_cap,
            values(sim, "uc_benefit_cap_reduction"),
            demand,
            values(sim, "uc_maximum_reduction"),
            PENNY_A_YEAR,
        )
        assigned = np.array([unit["draw"] < 0.4 for unit in units]) & claims
        np.testing.assert_allclose(
            deductions[assigned], expected[assigned], rtol=0, atol=1e-3
        )

    # 4. The components sum to the award before the cap.
    with_award = claims & (pre_cap > 0)
    total = (
        deductions
        + values(sim, "uc_benefit_cap_reduction_after_floor")
        + values(sim, "universal_credit")
    )
    np.testing.assert_allclose(
        total[with_award], pre_cap[with_award], rtol=0, atol=0.01
    )


def test_the_issue_example_takes_no_deductions_without_the_flag():
    # Reproducer for #2739: a supplied latent rate and an 85% floor gave
    # £720.25 of deductions to a unit whose flag is false.
    sim = Simulation(
        situation=situation([ISSUE_EXAMPLE], drawn=False), reform=floor_reform(0.85)
    )
    assert not values(sim, "uc_has_deduction")[0]
    assert values(sim, "uc_deductions")[0] == 0
    assert values(sim, "uc_benefit_cap_reduction_after_floor")[0] == pytest.approx(
        0.15 * STANDARD_ALLOWANCE, abs=0.01
    )
    assert values(sim, "universal_credit")[0] == pytest.approx(
        1_000 - 0.15 * STANDARD_ALLOWANCE, abs=0.01
    )


# Datasets: hashed draws, so the flag, rate and combination come from their
# formulas unless stored.


def _main_rule():
    """origin/main's uc_has_deduction, uc_deduction_rate and
    uc_advance_repayment_amount formulas at 7ed52038a, verbatim."""

    def estimated_advance_repayment_amount(benunit, period, parameters):
        p = parameters(period).gov.simulation.uc_deductions
        advance_share, _, _ = deduction_type_shares(benunit, period, parameters)
        latent = max_(benunit("uc_latent_deduction_rate", period), 0)
        return (
            min_(latent, p.calibration_cap)
            * advance_share
            * reference_standard_allowance(benunit, period, parameters)
        )

    class uc_has_deduction(Variable):
        def formula(benunit, period, parameters):
            p = parameters(period).gov.simulation.uc_deductions
            d = p.latent_rate_distribution
            incidence = (
                d.UNDER_5
                + d.AT_5
                + d.FIVE_TO_10
                + d.AT_10
                + d.TEN_TO_15
                + d.AT_15
                + d.FIFTEEN_TO_20
                + d.AT_20
                + d.TWENTY_TO_25
                + d.AT_25
                + d.OVER_25
            )
            region = benunit.household("region", period)
            adjusted_incidence = clip(
                incidence * p.region_incidence_factor[region], 0, 1
            )
            award = max_(
                benunit("universal_credit_pre_benefit_cap", period)
                - benunit("uc_benefit_cap_reduction", period),
                0,
            )
            on_uc = (
                benunit("claims_universal_credit", period)
                & (award > 0)
                & benunit("uc_award_carries_deductions", period)
            )
            draw = benunit("uc_deduction_random_draw", period)
            return on_uc & (draw < adjusted_incidence)

    class uc_advance_repayment_amount(Variable):
        def formula(benunit, period, parameters):
            return estimated_advance_repayment_amount(benunit, period, parameters)

    class uc_deduction_rate(Variable):
        def formula(benunit, period, parameters):
            law = parameters(period).gov.dwp.universal_credit.deductions
            calibration_cap = parameters(
                period
            ).gov.simulation.uc_deductions.calibration_cap
            _, third_share, government_share = deduction_type_shares(
                benunit, period, parameters
            )
            remaining_share = third_share * (
                not law.abolish.third_party
            ) + government_share * (not law.abolish.government)
            allowance = benunit("uc_standard_allowance", period)
            latent = benunit("uc_latent_deduction_rate", period)
            other_rate = min_(latent, calibration_cap) * remaining_share
            advance = benunit("uc_advance_repayment_amount", period)
            advance = where(
                advance >= 0,
                advance,
                estimated_advance_repayment_amount(benunit, period, parameters),
            )
            if law.abolish.advance:
                advance = 0
            advance_rate = np.divide(
                max_(advance, 0),
                allowance,
                out=np.zeros_like(allowance),
                where=allowance > 0,
            )
            above_cap_excess = max_(latent - calibration_cap, 0)
            return min_(advance_rate + other_rate, law.cap) + above_cap_excess

    class MAIN_RULE(Reform):
        def apply(self):
            for variable in (
                uc_has_deduction,
                uc_advance_repayment_amount,
                uc_deduction_rate,
            ):
                self.update_variable(variable)

    return MAIN_RULE


MAIN_RULE = _main_rule()

data_unit_strategy = st.fixed_dictionaries(
    {
        "pre_cap": st.integers(0, 2_000_000).map(lambda pennies: pennies / 100),
        # Gross cap as a share of the award, so many units are capped to nil.
        "cap_share": st.one_of(
            st.just(0.0), st.floats(0, 1.5, allow_nan=False), st.just(1.0)
        ),
        "region": st.sampled_from(REGIONS),
        "claims": st.booleans(),
    }
)


def tables(units, **benunit_columns):
    n = len(units)
    ids = np.arange(1, n + 1)
    pre_cap = np.array([unit["pre_cap"] for unit in units])
    person = pd.DataFrame(
        {
            "person_id": ids * 10,
            "person_benunit_id": ids,
            "person_household_id": ids,
            "age": np.full(n, 30),
        }
    )
    benunit = pd.DataFrame(
        {
            "benunit_id": ids,
            "would_claim_uc": np.array([unit["claims"] for unit in units]),
            "universal_credit_pre_benefit_cap": pre_cap,
            "uc_benefit_cap_reduction": pre_cap
            * np.array([unit["cap_share"] for unit in units]),
            **benunit_columns,
        }
    )
    household = pd.DataFrame(
        {
            "household_id": ids,
            "household_weight": np.full(n, 1_000.0),
            "region": np.array([unit["region"] for unit in units]),
        }
    )
    return UKMultiYearDataset(
        datasets=[
            UKSingleYearDataset(
                person=person, benunit=benunit, household=household, fiscal_year=YEAR
            )
        ]
    )


# Every region, a range of awards, and families the cap takes to nil, so the
# hashed draws assign some of each.
DATA_EXAMPLE = [
    dict(
        pre_cap=float(600 + 450 * i),
        cap_share=[0.0, 0.5, 1.0, 1.2][i % 4],
        region=REGIONS[i % len(REGIONS)],
        claims=i % 7 != 3,
    )
    for i in range(24)
]
COMPARED = (
    "uc_has_deduction",
    "uc_latent_deduction_rate",
    "uc_deduction_combination",
    "uc_advance_repayment_amount",
    "uc_deduction_rate",
    *DEDUCTION_OUTPUTS,
)

data_settings = settings(
    max_examples=2,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)


@data_settings
@given(units=st.lists(data_unit_strategy, min_size=1, max_size=24))
@example(units=DATA_EXAMPLE)
def test_current_law_formula_path_matches_main(units):
    head = Microsimulation(dataset=tables(units))
    main = Microsimulation(dataset=tables(units), reform=MAIN_RULE)
    for variable in COMPARED:
        np.testing.assert_array_equal(
            np.asarray(head.calculate(variable, YEAR)),
            np.asarray(main.calculate(variable, YEAR)),
            err_msg=variable,
        )


@data_settings
@given(
    units=st.lists(data_unit_strategy, min_size=1, max_size=24),
    floor=st.floats(0.5, 1.2, allow_nan=False),
)
@example(units=DATA_EXAMPLE, floor=0.85)
def test_a_floor_moves_only_the_split_for_families_capped_to_nil(units, floor):
    head = Microsimulation(dataset=tables(units), reform=floor_reform(floor))
    main = Microsimulation(
        dataset=tables(units), reform=(floor_reform(floor), MAIN_RULE)
    )
    pre_cap = values(head, "universal_credit_pre_benefit_cap")
    gross_cap = values(head, "uc_benefit_cap_reduction")
    capped_to_nil = gross_cap >= pre_cap
    changed = values(head, "uc_has_deduction") != values(main, "uc_has_deduction")
    # Only families the cap takes to nil gain the flag.
    assert np.all(capped_to_nil[changed])
    assert np.all(values(head, "uc_has_deduction")[changed])
    for variable in ("uc_deductions", "uc_benefit_cap_reduction_after_floor"):
        np.testing.assert_array_equal(
            values(head, variable)[~changed], values(main, variable)[~changed]
        )
    gain = values(head, "universal_credit") - values(main, "universal_credit")
    assert np.all(gain >= -1e-3)
    assert np.all(gain <= PENNY_A_YEAR + 1e-3)
    np.testing.assert_allclose(gain[~changed], 0, atol=1e-6)


def microcosm_style(units, floor):
    """The formula path, and a dataset storing its draws with a latent rate
    and combination for every unit the draw assigns, claimant or not. The
    dataset comes as a function, since building a simulation encodes its
    enum columns in place."""
    formula = Microsimulation(dataset=tables(units), reform=floor_reform(floor))
    draw = values(formula, "uc_deduction_random_draw")
    parameters = formula.tax_benefit_system.parameters(f"{YEAR}-01-01")
    p = parameters.gov.simulation.uc_deductions
    d = p.latent_rate_distribution
    incidence = (
        d.UNDER_5
        + d.AT_5
        + d.FIVE_TO_10
        + d.AT_10
        + d.TEN_TO_15
        + d.AT_15
        + d.FIFTEEN_TO_20
        + d.AT_20
        + d.TWENTY_TO_25
        + d.AT_25
        + d.OVER_25
    )
    factor = np.array(
        [getattr(p.region_incidence_factor, unit["region"]) for unit in units]
    )
    assigned = draw < np.clip(incidence * factor, 0, 1)
    every_assigned = Microsimulation(dataset=tables(units, uc_has_deduction=assigned))
    columns = dict(
        uc_deduction_random_draw=draw,
        uc_deduction_type_random_draw=values(formula, "uc_deduction_type_random_draw"),
        uc_latent_deduction_rate=values(every_assigned, "uc_latent_deduction_rate"),
        # Microsimulation results carry enum names, as a dataset stores them.
        uc_deduction_combination=values(every_assigned, "uc_deduction_combination"),
    )
    return formula, lambda: tables(units, **columns)


@data_settings
@given(
    units=st.lists(data_unit_strategy, min_size=1, max_size=24),
    floor=floor_strategy,
)
@example(units=DATA_EXAMPLE, floor=0.85)
@example(units=DATA_EXAMPLE, floor=0.0)
def test_stored_attributes_give_the_formula_path(units, floor):
    formula, stored_dataset = microcosm_style(units, floor)
    stored = Microsimulation(dataset=stored_dataset(), reform=floor_reform(floor))
    for variable in ("uc_has_deduction", *DEDUCTION_OUTPUTS):
        np.testing.assert_allclose(
            values(stored, variable),
            values(formula, variable),
            rtol=0,
            atol=1e-6,
            err_msg=variable,
        )


def test_lowering_incidence_reaches_stored_rates():
    # A dataset that stores latent rates still answers a cut in incidence:
    # the reformed flag drops some units, and their stored rates no longer
    # count. On origin/main the stored rates kept every deduction.
    _, stored_dataset = microcosm_style(DATA_EXAMPLE, 0.0)
    stored = Microsimulation(dataset=stored_dataset())
    cut = {
        f"gov.simulation.uc_deductions.region_incidence_factor.{region}": {
            f"{YEAR}-01-01.{YEAR}-12-31": 0.3
        }
        for region in REGIONS
    }
    reformed = Microsimulation(dataset=stored_dataset(), reform=cut)
    before = values(stored, "uc_deductions") > 0
    after = values(reformed, "uc_deductions") > 0
    flag = values(reformed, "uc_has_deduction").astype(bool)
    assert np.all(flag[after])
    assert after.sum() < before.sum()
