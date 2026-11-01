"""Properties of the savings-credit-only Housing Benefit income calculation.

SI 2006/214 reg 27(4) (NI: SR 2006/406 reg 25(4)) permits the following
earnings modifications to the Pension Service's net income assessment:

I1. The residual treated as additional earnings disregard is exactly the
    Schedule 4 para 9(1) amount included in the applicable disregard: zero or
    the annual para 9 amount. It contains no part of the applied standard.
I2. The standard-related modification is zero unless the family is a lone
    parent or has permitted work. Otherwise it is the positive excess of
    the applied standard over the Pension Credit earnings disregard.
I3. Income is non-negative and equals Pension Credit income plus savings
    credit payable, less childcare, maintenance and those earnings
    modifications, with a floor at zero.
I4. Increasing either the Pension Credit earnings disregard or Pension
    Credit income, with all other inputs fixed, never lowers HB income.
I5. Ordinary families (no permitted work, no lone parent and no special
    route) agree with main's ordinary-standard subtraction formula.

These are fixture-scale pension-age populations, without passporting or
the working-age accommodation disregard. War pension income is fixed at
zero. Earnings, childcare and Pension Credit figures are pre-assessed
inputs: this isolates reg 27 rather than retesting their upstream rules.
Pension Credit earnings disregards may exceed today's statutory amounts as
independent reform/metamorphic controls. In I1 a high disregard disables the
standard-excess modification and a high income prevents clipping, exposing
the actual residual used by the savings-credit formula. This also catches
an omitted lone-parent proviso even when errors in the two modifications
would cancel at the current Pension Credit lone-parent disregard.
"""

import numpy as np
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_core.simulations import Simulation
from policyengine_uk.system import system

YEAR = 2026
WEEKS = 52
TOLERANCE = 0.01
HIGH_AMOUNT = 50_000
SHAPES = {
    "single": (1, 0),
    "couple": (2, 0),
    "lone_parent": (1, 1),
    "couple_with_children": (2, 1),
}
P = system.parameters(YEAR).gov.dwp.housing_benefit.means_test.income_disregard
PARA_9 = P.worker * WEEKS
PROPERTY_SETTINGS = settings(
    max_examples=5,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


def case(**overrides):
    result = dict(
        shape="couple",
        net=2_000.0,
        special=False,
        permitted=0.0,
        worker=True,
        childcare=0.0,
        pc_disregard=1_040.0,
        pc_income=20_000.0,
        savings_credit=500.0,
        maintenance=0.0,
    )
    result.update(overrides)
    return result


def components(unit):
    """Independent statutory standard and para 9 amounts, in annual pounds."""
    lone_parent = unit["shape"] == "lone_parent"
    if lone_parent:
        weekly = P.lone_parent
    elif unit["special"]:
        weekly = P.special
    elif SHAPES[unit["shape"]][0] == 2:
        weekly = P.couple
    else:
        weekly = P.single
    selected = min(unit["net"], weekly * WEEKS)
    permitted = max(0, unit["permitted"])
    # Sch 4 para 5A(2): permitted work replaces the standard, except that
    # the lone parent retains para 2 when it is higher; earnings cap both.
    standard = (
        min(unit["net"], max(permitted, selected if lone_parent else 0))
        if permitted > 0
        else selected
    )
    # Para 9(3)(a): earnings must "equal or exceed" the other disregards,
    # deductible childcare and para 9 itself, compared in statutory pence.
    covers_additional = round(unit["net"] * 100) >= round(
        (standard + unit["childcare"] + PARA_9) * 100
    )
    additional = PARA_9 if unit["worker"] and covers_additional else 0
    excess = (
        max(0, standard - unit["pc_disregard"]) if lone_parent or permitted > 0 else 0
    )
    return standard, additional, excess


@st.composite
def families(draw, ordinary=False):
    shape = draw(
        st.sampled_from(
            ["single", "couple", "couple_with_children"] if ordinary else sorted(SHAPES)
        )
    )
    return case(
        shape=shape,
        net=draw(st.integers(0, 2_000_000)) / 100,
        special=False if ordinary else draw(st.booleans()),
        permitted=(
            0
            if ordinary
            else draw(
                st.one_of(
                    st.sampled_from(
                        [-1, 0, 500, 1_040, 1_299.99, 1_300, 1_300.01, 9_542]
                    ),
                    st.integers(-100, 2_000_000).map(lambda pennies: pennies / 100),
                )
            )
        ),
        worker=draw(st.booleans()),
        childcare=(draw(st.integers(0, 800_000)) / 100 if SHAPES[shape][1] else 0),
        pc_disregard=draw(st.integers(0, 2_000_000)) / 100,
        pc_income=draw(st.integers(0, 5_000_000)) / 100,
        savings_credit=draw(st.integers(0, 200_000)) / 100,
        maintenance=(draw(st.integers(0, 78_000)) / 100 if SHAPES[shape][1] else 0),
    )


# Exercise all family shapes, selected standards, the earnings cap, positive
# permitted work on either side of the lone-parent amount, and para 9 off/on.
EDGE_CASES = [
    case(shape=shape, special=special, net=net, permitted=permitted, worker=worker)
    for shape in SHAPES
    for special in (False, True)
    for net, permitted in (
        (0, 9_542),
        (259.99, 0),
        (500, 1_040),
        (2_000, 0),
        (2_000, 1_040),
        (2_000, 1_299.99),
        (2_000, 1_300),
        (2_000, 1_300.01),
        (9_542, 20_000),
        (20_000, 9_542),
    )
    for worker in (False, True)
]
for shape in SHAPES:
    for special in (False, True):
        for permitted in (0, 1_040, 9_542):
            unit = case(shape=shape, special=special, net=20_000, permitted=permitted)
            standard = components(unit)[0]
            for delta in (-0.01, 0, 0.01):
                EDGE_CASES.append(case(**{**unit, "net": standard + PARA_9 + delta}))
EDGE_CASES.extend(
    [
        case(shape="lone_parent", permitted=1_040, pc_disregard=1_560),
        case(shape="lone_parent", permitted=2_080, pc_disregard=1_560),
        case(
            shape="couple_with_children",
            pc_income=0,
            childcare=8_000,
            maintenance=780,
        ),
    ]
)
ORDINARY_CASES = [
    unit
    for unit in EDGE_CASES
    if unit["shape"] != "lone_parent" and not unit["special"] and unit["permitted"] == 0
]
POPULATIONS = st.lists(families(), min_size=1, max_size=24)


def calculate(units, pc_income=None, pc_disregard=None):
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        n_adults, n_children = SHAPES[unit["shape"]]
        members = []
        for j in range(n_adults + n_children):
            name = f"p{i}_{j}"
            people[name] = {
                "age": {YEAR: 80 if j < n_adults else 8},
                "is_claimant_or_partner": {YEAR: j < n_adults},
            }
            members.append(name)
        benunits[f"b{i}"] = {"members": members}
        households[f"h{i}"] = {"members": members}
    # These pre-assessed fixtures share read-only rules; each new core
    # simulation keeps independent holders without UK wrapper data/scenarios.
    sim = Simulation(
        tax_benefit_system=system,
        situation={"people": people, "benunits": benunits, "households": households},
    )
    inputs = {
        "housing_benefit_net_earnings": "net",
        "housing_benefit_special_earnings_disregard_eligible": "special",
        "housing_benefit_permitted_work_disregard": "permitted",
        "meets_housing_benefit_additional_earnings_disregard_conditions": "worker",
        "housing_benefit_applicable_income_childcare_element": "childcare",
        "pension_credit_earnings_disregard": "pc_disregard",
        "pension_credit_income": "pc_income",
        "pension_credit": "savings_credit",
        "housing_benefit_maintenance_disregard": "maintenance",
    }
    for variable, key in inputs.items():
        values = [unit[key] for unit in units]
        if key == "pc_income" and pc_income is not None:
            values = np.full(len(units), pc_income)
        if key == "pc_disregard" and pc_disregard is not None:
            values = np.full(len(units), pc_disregard)
        sim.set_input(variable, YEAR, values)
    for variable, value in (
        ("housing_benefit_specified_or_temporary_accommodation_disregard", 0),
        ("housing_benefit_on_passporting_benefit", False),
        ("pension_credit_war_pension_income", 0),
    ):
        sim.set_input(variable, YEAR, np.full(len(units), value))
    return {
        key: np.asarray(sim.calculate(variable, YEAR), dtype=float)
        for key, variable in {
            "income": "housing_benefit_savings_credit_only_income",
            "applicable_disregard": "housing_benefit_applicable_income_disregard",
            "standard": "housing_benefit_applied_standard_earnings_disregard",
        }.items()
    }


@PROPERTY_SETTINGS
@given(units=POPULATIONS)
@example(units=EDGE_CASES)
def test_i1_para_9_is_isolated_exactly(units):
    values = calculate(units, pc_income=HIGH_AMOUNT, pc_disregard=HIGH_AMOUNT)
    for i, unit in enumerate(units):
        standard, para_9, _ = components(unit)
        assert abs(values["standard"][i] - standard) < TOLERANCE, unit
        included_para_9 = values["applicable_disregard"][i] - values["standard"][i]
        assert abs(included_para_9 - para_9) < TOLERANCE, unit
        # With the standard excess disabled, infer the actual residual used
        # by the savings-credit path rather than merely recomputing one.
        observed_residual = (
            HIGH_AMOUNT
            + unit["savings_credit"]
            - unit["childcare"]
            - unit["maintenance"]
            - values["income"][i]
        )
        assert abs(observed_residual - included_para_9) < TOLERANCE, (
            unit,
            observed_residual,
            included_para_9,
        )


@PROPERTY_SETTINGS
@given(units=POPULATIONS)
@example(units=EDGE_CASES)
def test_i2_only_allowed_standard_excess_is_deducted(units):
    values = calculate(units, pc_income=HIGH_AMOUNT)
    for i, unit in enumerate(units):
        _, para_9, excess = components(unit)
        observed_excess = (
            HIGH_AMOUNT
            + unit["savings_credit"]
            - unit["childcare"]
            - unit["maintenance"]
            - para_9
            - values["income"][i]
        )
        assert abs(observed_excess - excess) < TOLERANCE, (
            unit,
            observed_excess,
            excess,
        )
        if unit["shape"] != "lone_parent" and unit["permitted"] <= 0:
            assert abs(observed_excess) < TOLERANCE, unit


@PROPERTY_SETTINGS
@given(units=POPULATIONS)
@example(units=EDGE_CASES)
def test_i3_income_is_non_negative_and_has_only_listed_modifications(units):
    values = calculate(units)
    for i, unit in enumerate(units):
        _, para_9, excess = components(unit)
        expected = max(
            0,
            unit["pc_income"]
            + unit["savings_credit"]
            - unit["childcare"]
            - unit["maintenance"]
            - para_9
            - excess,
        )
        assert values["income"][i] >= 0, unit
        assert abs(values["income"][i] - expected) < TOLERANCE, (
            unit,
            values["income"][i],
            expected,
        )


@PROPERTY_SETTINGS
@given(units=POPULATIONS, bump=st.integers(1, 1_000_000).map(lambda p: p / 100))
@example(units=EDGE_CASES, bump=520)
def test_i4_income_is_non_decreasing_in_pc_earnings_disregard(units, bump):
    bumped_units = [
        {**unit, "pc_disregard": unit["pc_disregard"] + bump} for unit in units
    ]
    # Each family has separate entities, so one vector preserves the same
    # before/after controls without constructing the model twice.
    income = calculate(units + bumped_units)["income"]
    before, after = income[: len(units)], income[len(units) :]
    for i, unit in enumerate(units):
        assert after[i] >= before[i] - TOLERANCE, (unit, bump, before[i], after[i])


@PROPERTY_SETTINGS
@given(units=POPULATIONS, bump=st.integers(1, 1_000_000).map(lambda p: p / 100))
@example(units=EDGE_CASES, bump=520)
def test_i4_income_is_non_decreasing_in_pc_income(units, bump):
    bumped_units = [{**unit, "pc_income": unit["pc_income"] + bump} for unit in units]
    # Each family has separate entities, so one vector preserves the same
    # before/after controls without constructing the model twice.
    income = calculate(units + bumped_units)["income"]
    before, after = income[: len(units)], income[len(units) :]
    for i, unit in enumerate(units):
        assert after[i] >= before[i] - TOLERANCE, (unit, bump, before[i], after[i])


@PROPERTY_SETTINGS
@given(units=st.lists(families(ordinary=True), min_size=1, max_size=24))
@example(units=ORDINARY_CASES)
def test_i5_ordinary_families_agree_with_main_formula(units):
    values = calculate(units)
    for i, unit in enumerate(units):
        # origin/main's formula subtracts the ordinary standard from the
        # applicable disregard to isolate para 9; its lone-parent term is
        # zero for this deliberately restricted population.
        ordinary_weekly = P.couple if SHAPES[unit["shape"]][0] == 2 else P.single
        ordinary_standard = min(unit["net"], ordinary_weekly * WEEKS)
        main_additional = max(0, values["applicable_disregard"][i] - ordinary_standard)
        expected = max(
            0,
            unit["pc_income"]
            + unit["savings_credit"]
            - unit["childcare"]
            - unit["maintenance"]
            - main_additional,
        )
        assert abs(values["income"][i] - expected) < TOLERANCE, (
            unit,
            values["income"][i],
            expected,
        )
