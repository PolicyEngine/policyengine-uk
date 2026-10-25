"""Parameter-gated structural reforms follow their calculation periods.

Issue #1800 concerns constructor dispatch, which the policy YAML runner's
explicit reform classes bypass. These public Simulation cases therefore use
dated dictionaries and equivalent Scenario construction. They preserve the
existing contributed formulas, rather than asserting new statutory policy.

The current expanded-MA formula deducts its transfer from earned taxable
income: at GBP80,000 the GBP1,260 transfer saves GBP504 at 40%, not a GBP252
basic-rate credit. The reported-only cases declare synthetic survey reports;
their isolated payments are not claims of natural statutory entitlement.
"""

import copy
import math

import numpy as np
import pandas as pd
import pytest

from policyengine_uk import Simulation
from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.reforms.cps.marriage_tax_reforms import (
    expanded_ma_reform,
    marriage_neutral_it_reform,
)
from policyengine_uk.utils.scenario import Scenario


YEARS = (2025, 2026, 2027)
CPS = "gov.contrib.cps.marriage_tax_reforms"
EXPAND = f"{CPS}.expanded_ma.remove_income_condition"
MA_RATE = f"{CPS}.expanded_ma.ma_rate"
MA_CHILD_AGE = f"{CPS}.expanded_ma.max_child_age"
NEUTRAL = f"{CPS}.marriage_neutral_it.neutralise_income_tax"
HOUSEHOLD_HICBC = "gov.contrib.conservatives.cb_hitc_household"
SCP = "gov.contrib.scotland.scottish_child_payment.in_effect"
REPORTED_ONLY = "gov.contrib.policyengine.disable_simulated_benefits"
FY2026 = "2026-04-06.2027-04-05"


@pytest.fixture(params=("dict", "scenario"))
def route(request):
    return request.param


def annual(value, years=YEARS):
    return {year: value for year in years}


def construct(situation=None, changes=None, route="dict", dataset=None):
    kwargs = (
        {"situation": copy.deepcopy(situation)} if situation else {"dataset": dataset}
    )
    if changes:
        if route == "dict":
            kwargs["reform"] = changes
        else:
            kwargs["scenario"] = Scenario.from_reform(changes)
    simulation = Simulation(**kwargs)
    assert simulation.default_input_period == 2025
    return simulation


def money(simulation, variable, year):
    return np.asarray(simulation.calculate(variable, year), dtype=float)


def equals(actual, expected):
    np.testing.assert_allclose(actual, expected, rtol=0, atol=0.01)


def couple(earnings=(80_000, 0), child=False, region="LONDON", years=YEARS):
    people = {}
    for index, income in enumerate(earnings):
        people[f"person{index + 1}"] = {
            "age": {year: year - (1985 + index) for year in years},
            "date_of_birth": annual((1985 + index) * 10_000 + 1006, years),
            "employment_income": annual(income, years),
            "marital_status": annual("MARRIED", years),
            "would_claim_marriage_allowance": annual(True, years),
        }
    if child:
        people["child1"] = {
            "age": {year: year - 2015 for year in years},
            "date_of_birth": annual(20151006, years),
            "employment_income": annual(0, years),
            "marital_status": annual("SINGLE", years),
            "would_claim_scp": annual(True, years),
        }
    members = list(people)
    return {
        "people": people,
        "benunits": {
            "benunit": {
                "members": members,
                "is_married": annual(True, years),
                "would_claim_child_benefit": annual(True, years),
                "child_benefit_opts_out": annual(False, years),
            }
        },
        "households": {
            "household": {"members": members, "region": annual(region, years)}
        },
    }


def scp_family(year, age=0, region="SCOTLAND", takes_up=True):
    """An explicit October6 birthday agrees with the supplied annual age."""
    return {
        "people": {
            "person1": {
                "age": {year: 40},
                "date_of_birth": {year: (year - 40) * 10_000 + 1006},
            },
            "child1": {
                "age": {year: age},
                "date_of_birth": {year: (year - age) * 10_000 + 1006},
                "would_claim_scp": {year: takes_up},
            },
        },
        "benunits": {
            "benunit": {
                "members": ["person1", "child1"],
                # A declared qualifying award; SCP itself is not overridden.
                "universal_credit": {year: 5_000},
            }
        },
        "households": {
            "household": {"members": ["person1", "child1"], "region": {year: region}}
        },
    }


def reported_dataset():
    """Three public adults, with all ten supported years supplied explicitly."""
    datasets = []
    for year in range(2025, 2035):
        roles = [True, False, True] if year == 2026 else [True, True, False]
        multiplier = 1 if year == 2025 else 10
        person = pd.DataFrame(
            {
                "person_id": [1, 2, 3],
                "person_benunit_id": [1, 1, 1],
                "person_household_id": [1, 1, 1],
                "age": [40.0, 39.0, 30.0],
                "is_claimant_or_partner": roles,
                "child_benefit_reported": np.array([111.0, 222.0, 333.0]) * multiplier,
                "esa_income_reported": np.array([100.0, 200.0, 300.0]) * multiplier,
                "carers_allowance_reported": [4_000.0, 0.0, 0.0],
                "care_hours": [40.0, 0.0, 0.0],
            }
        )
        datasets.append(
            UKSingleYearDataset(
                person=person,
                benunit=pd.DataFrame({"benunit_id": [1]}),
                household=pd.DataFrame(
                    {
                        "household_id": [1],
                        "region": ["SCOTLAND" if year == 2026 else "LONDON"],
                        "household_weight": [1.0],
                        "tenure_type": ["OWNED_OUTRIGHT"],
                        "rent": [0.0],
                        "council_tax": [0.0],
                    }
                ),
                fiscal_year=year,
            )
        )
    return UKMultiYearDataset(datasets=datasets)


def test_future_expanded_ma_applies_only_inside_interval(route):
    """12570 x10%, rounded up to10, gives1260; higher-rate tax falls504."""
    simulation = construct(couple(), {EXPAND: {FY2026: True}}, route)
    for year in YEARS:
        active = year == 2026
        equals(
            money(simulation, "marriage_allowance", year), [1_260 if active else 0, 0]
        )
        # Existing earned-income deduction:7540 + (80000-12570-37700-MA)*40%.
        equals(money(simulation, "income_tax", year), [18_928 if active else 19_432, 0])


def test_expanded_ma_child_limit_follows_calculation_period():
    changes = {
        EXPAND: {"2025-04-06.2028-04-05": True},
        MA_CHILD_AGE: {"2025": 5, "2026": 15, "2027": 5},
    }
    simulation = construct(couple(child=True), changes)
    for year in YEARS:
        equals(
            money(simulation, "marriage_allowance", year),
            [1_260 if year == 2026 else 0, 0, 0],
        )


def test_expanded_ma_rate_only_later_change_preserves_off_year_statutory_cap(route):
    simulation = construct(couple(), {MA_RATE: {FY2026: 0.2}}, route)
    for year in YEARS:
        active = year == 2026
        # The reform's own20% cap is2520 after rounding, saving1008 at40%.
        equals(
            money(simulation, "marriage_allowance", year), [2_520 if active else 0, 0]
        )
        equals(money(simulation, "income_tax", year), [18_424 if active else 19_432, 0])


def test_statutory_marriage_allowance_rate_alone_does_not_activate_cps():
    statutory = "gov.hmrc.income_tax.allowances.marriage_allowance.max"
    simulation = construct(couple(), {statutory: {FY2026: 0.0}})
    for year in YEARS:
        equals(money(simulation, "marriage_allowance", year), [0, 0])
        equals(money(simulation, "income_tax", year), [19_432, 0])


def test_marriage_neutral_income_tax_applies_only_inside_interval(route):
    simulation = construct(couple(), {NEUTRAL: {FY2026: True}}, route)
    for year in YEARS:
        active = year == 2026
        equals(
            money(simulation, "net_income", year),
            [40_000, 40_000] if active else [80_000, 0],
        )
        # Each spouse pays(40000-12570)*20%=5486 after an advantageous split.
        equals(
            money(simulation, "income_tax", year),
            [5_486, 5_486] if active else [19_432, 0],
        )


def test_household_hicbc_applies_only_inside_interval(route):
    simulation = construct(
        couple((45_000, 45_000), child=True), {HOUSEHOLD_HICBC: {FY2026: True}}, route
    )
    for year in YEARS:
        child_benefit = float(money(simulation, "child_benefit", year).sum())
        assert child_benefit > 0
        # Each individual is below60000; combined90000 exceeds80000, so the
        # household reform charges100% of CB, rounded down to whole pounds.
        expected = math.floor(round(child_benefit, 2)) if year == 2026 else 0
        assert money(simulation, "CB_HITC", year).sum() == pytest.approx(
            expected, abs=0.01
        )


def test_scp_activation_beyond_old_discovery_window(route):
    changes = {SCP: {"2035-04-06.2036-04-05": True}}
    for year in (2034, 2035, 2036):
        # Each independent household contains an explicitly dated under-one
        # child that year; no future DOB is assigned to an earlier year.
        simulation = construct(scp_family(year), changes, route)
        p = simulation.tax_benefit_system.parameters(year)
        weekly = (
            p.gov.contrib.scotland.scottish_child_payment.under_one
            if year == 2035
            else p.gov.social_security_scotland.scottish_child_payment.amount
        )
        equals(money(simulation, "scottish_child_payment", year), [0, 52 * weekly])


@pytest.mark.parametrize(
    "control", ("false", "age_one", "outside_scotland", "no_takeup")
)
def test_scp_off_age_location_and_takeup_controls(control):
    year = 2035
    changes = {SCP: {"2035-04-06.2036-04-05": control != "false"}}
    situation = scp_family(
        year,
        age=1 if control == "age_one" else 0,
        region="LONDON" if control == "outside_scotland" else "SCOTLAND",
        takes_up=control != "no_takeup",
    )
    simulation = construct(situation, changes)
    weekly = simulation.tax_benefit_system.parameters(
        year
    ).gov.social_security_scotland.scottish_child_payment.amount
    expected = 0 if control in ("outside_scotland", "no_takeup") else 52 * weekly
    equals(money(simulation, "scottish_child_payment", year), [0, expected])


def test_reported_only_switch_writes_only_active_dataset_years(route):
    simulation = construct(
        changes={REPORTED_ONLY: {FY2026: True}}, route=route, dataset=reported_dataset()
    )
    for year in YEARS:
        # No children: the natural CB entitlement is0. The mode substitutes
        # only2026's666 base-year report, not its6660 later-year reports.
        equals(money(simulation, "child_benefit", year), [666 if year == 2026 else 0])
    recorded = {
        str(period)
        for variable, _, period in simulation._user_input_keys
        if variable == "child_benefit"
    }
    assert recorded == {"2026"}


def test_reported_only_period_role_and_country_mapping_is_preserved():
    changes = {REPORTED_ONLY: {FY2026: True}}
    simulation = construct(changes=changes, dataset=reported_dataset())
    # Current-year roles choose members1+3, but the amounts come from2025.
    equals(money(simulation, "esa_income", 2026), [600])
    equals(money(simulation, "claimant_or_partner_esa_income", 2026), [400])
    # The single4000 report moves to Scotland's CSP only in the active year.
    equals(money(simulation, "carers_allowance", 2026), [0, 0, 0])
    equals(money(simulation, "carer_support_payment", 2026), [4_000, 0, 0])
    baseline = construct(dataset=reported_dataset())
    for year in (2025, 2027):
        for variable in (
            "esa_income",
            "claimant_or_partner_esa_income",
            "carers_allowance",
            "carer_support_payment",
        ):
            equals(money(simulation, variable, year), money(baseline, variable, year))


def test_disjoint_true_false_true_intervals_restore_original_outputs():
    changes = {EXPAND: {"2025": True, "2026": False, "2027": True}}
    simulation = construct(couple(), changes)
    for year in YEARS:
        active = year != 2026
        equals(
            money(simulation, "marriage_allowance", year), [1_260 if active else 0, 0]
        )
        equals(money(simulation, "income_tax", year), [18_928 if active else 19_432, 0])


def test_reverse_query_order_baseline_instances_and_clones_are_isolated():
    simulation = construct(couple(), {EXPAND: {FY2026: True}})
    clone = simulation.clone()
    branch = simulation.get_branch("period_control", clone_system=True)
    for year in (2027, 2025, 2026):
        expected = [1_260 if year == 2026 else 0, 0]
        for item in (simulation, clone, branch):
            equals(money(item, "marriage_allowance", year), expected)
        equals(money(simulation.baseline, "marriage_allowance", year), [0, 0])
    fresh = construct(couple())
    equals(money(fresh, "marriage_allowance", 2026), [0, 0])
    # A branch's genuine user override stays branch-local.
    branch.set_input("employment_income", 2026, [60_000, 0])
    equals(money(simulation, "employment_income", 2026), [80_000, 0])
    equals(money(clone, "employment_income", 2026), [80_000, 0])


def test_independent_dated_switches_compose_without_losing_either():
    interval = "2027-04-06.2028-04-05"
    changes = {HOUSEHOLD_HICBC: {interval: True}, SCP: {interval: True}}
    for year in (2026, 2027, 2028):
        situation = couple(
            (45_000, 45_000), child=True, region="SCOTLAND", years=(year,)
        )
        situation["people"]["child1"].update(
            age={year: 0}, date_of_birth={year: year * 10_000 + 1006}
        )
        situation["benunits"]["benunit"]["universal_credit"] = {year: 5_000}
        simulation = construct(situation, changes)
        cb = float(money(simulation, "child_benefit", year).sum())
        expected_charge = math.floor(round(cb, 2)) if year == 2027 else 0
        assert money(simulation, "CB_HITC", year).sum() == pytest.approx(
            expected_charge, abs=0.01
        )
        p = simulation.tax_benefit_system.parameters(year)
        weekly = (
            p.gov.contrib.scotland.scottish_child_payment.under_one
            if year == 2027
            else p.gov.social_security_scotland.scottish_child_payment.amount
        )
        equals(money(simulation, "scottish_child_payment", year), [0, 0, 52 * weekly])


@pytest.mark.parametrize("kind", ("expanded_ma", "neutral"))
def test_direct_bypass_reform_interfaces_keep_their_existing_behavior(kind):
    reform = expanded_ma_reform if kind == "expanded_ma" else marriage_neutral_it_reform
    simulation = Simulation(situation=couple(), reform=reform)
    if kind == "expanded_ma":
        equals(money(simulation, "marriage_allowance", 2026), [1_260, 0])
        equals(money(simulation, "income_tax", 2026), [18_928, 0])
    else:
        equals(money(simulation, "net_income", 2026), [40_000, 40_000])
        equals(money(simulation, "income_tax", 2026), [5_486, 5_486])


# Additional public ownership/context controls for the period-scoped input
# overlay. The original twenty-four cases above remain unchanged.
def test_reported_mode_equal_value_genuine_replacement_survives_off_year():
    from policyengine_core.periods import period as period_

    for direct_holder, same_object in ((False, False), (True, True)):
        simulation = construct(
            changes={REPORTED_ONLY: {FY2026: True}}, dataset=reported_dataset()
        )
        value = simulation.calculate("child_benefit", 2026)
        equals(value, [666])
        genuine = value if same_object else np.array([666], dtype=value.dtype)
        if direct_holder:
            simulation.get_holder("child_benefit").set_input(
                period_(2026),
                genuine,
                branch_name=simulation.branch_name,
            )
        else:
            simulation.set_input("child_benefit", 2026, genuine)
        Scenario(parameter_changes={REPORTED_ONLY: False}).apply(simulation)
        equals(money(simulation, "child_benefit", 2027), [0])
        equals(money(simulation, "child_benefit", 2026), [666])
        assert any(
            name == "child_benefit" and str(period) == "2026"
            for name, _, period in simulation._user_input_keys
        )
        simulation.set_input("child_benefit", 2026, np.array([0.0]))
        equals(money(simulation, "child_benefit", 2026), [0])
        assert any(
            name == "child_benefit" and str(period) == "2026"
            for name, _, period in simulation._user_input_keys
        )


def test_reported_mode_nested_requested_periods_restore_caller_state():
    from policyengine_uk.model_api import BenUnit, Reform, Variable, YEAR

    class active_period_probe(Variable):
        label = "Public active-period transition probe"
        entity = BenUnit
        definition_period = YEAR
        value_type = float

        def formula(benunit, period):
            simulation = benunit.simulation
            # A real active -> inactive -> active transition within the
            # inactive outer request. All people in this fixture are adults.
            active = simulation.calculate("child_benefit", 2026)
            inactive = simulation.calculate("child_benefit", 2027)
            return active + inactive + simulation.calculate("child_benefit", 2026)

    class inactive_period_probe(Variable):
        label = "Public inactive-period transition probe"
        entity = BenUnit
        definition_period = YEAR
        value_type = float

        def formula(benunit, period):
            return benunit.simulation.calculate("active_period_probe", 2026) + benunit(
                "child_benefit", period
            )

    class probes(Reform):
        def apply(self):
            self.add_variable(active_period_probe)
            self.add_variable(inactive_period_probe)

    simulation = construct(
        changes={REPORTED_ONLY: {FY2026: True}}, dataset=reported_dataset()
    )
    simulation.apply_reform(probes)
    # 666 + 0 + 666 from declared reports, plus natural no-child CB0.
    for _ in range(2):
        equals(money(simulation, "inactive_period_probe", 2027), [1332])
        equals(money(simulation, "child_benefit", 2027), [0])
        equals(money(simulation, "child_benefit", 2026), [666])


def test_reported_mode_clone_exception_finally_keeps_genuine_inputs():
    from policyengine_uk.model_api import BenUnit, Reform, Variable, YEAR

    class failing_period_probe(Variable):
        label = "Public cross-year exception probe"
        entity = BenUnit
        definition_period = YEAR
        value_type = float

        def formula(benunit, period):
            simulation = benunit.simulation
            equals(money(simulation, "child_benefit", 2026), [666])
            equals(money(simulation, "child_benefit", 2027), [0])
            # This genuine replacement occurs WHILE the inactive outer
            # context is suspended, not merely before the failing query.
            simulation.set_input("child_benefit", 2026, [999])
            raise ValueError("reported-mode public cross-year probe")

    class probe(Reform):
        def apply(self):
            self.add_variable(failing_period_probe)

    parent = construct(
        changes={REPORTED_ONLY: {FY2026: True}}, dataset=reported_dataset()
    )
    clone = parent.clone()
    clone.apply_reform(probe)
    with pytest.raises(ValueError, match="^reported-mode public cross-year probe$"):
        clone.calculate("failing_period_probe", 2027)
    equals(money(clone, "child_benefit", 2026), [999])
    equals(money(parent, "child_benefit", 2026), [666])
    for simulation in (parent, clone):
        equals(money(simulation, "child_benefit", 2027), [0])
    # An equal genuine write before cloning must also cease being model-owned.
    parent.set_input("child_benefit", 2026, [666])
    branch = parent.get_branch("genuine_reported_control", clone_system=True)
    Scenario(parameter_changes={REPORTED_ONLY: False}).apply(branch)
    equals(money(branch, "child_benefit", 2026), [666])
    equals(money(parent, "child_benefit", 2026), [666])


# DRAFT supplemental engineering regressions. These are not adopted or run.
@pytest.mark.parametrize(
    "history,expected",
    (
        ({"0000-01-01": False, "2026-01-01": True, "2027-01-01": None}, None),
        ({"0000-01-01": False, "2026-01-01": False}, False),
        ({"0000-01-01": False, "2026-01-01": True, "2027-01-01": False}, True),
    ),
    ids=("true_then_null_rejected", "all_false", "true_then_false_available"),
)
def test_structural_discovery_validates_complete_real_parameter_history(
    history, expected
):
    from policyengine_core.parameters import Parameter
    from policyengine_uk.reforms.reforms import finite_parameter_activation

    # Real Parameter parsing preserves the literal None and raw sentinel.
    # The literal oracle requires complete supported history, not just one
    # available interval. No Simulation/converter null-survival is assumed.
    leaf = Parameter("structural_history_probe", data=history)
    assert [(entry.instant_str, entry.value) for entry in leaf.values_list] == sorted(
        history.items(), reverse=True
    )
    if expected is None:
        assert leaf._get_at_instant("2027-01-01") is None
        with pytest.raises(
            ValueError, match="^Structural reform parameter has no value at 2027-01-01$"
        ):
            finite_parameter_activation([leaf], lambda values: values[0])
    else:
        assert finite_parameter_activation([leaf], lambda values: values[0]) is expected


@pytest.mark.parametrize(
    "completion,delete",
    (("return", True), ("exception", True), ("return", False), ("exception", False)),
    ids=("delete_return", "delete_exception", "control_return", "control_exception"),
)
def test_reported_mode_direct_holder_absent_delete_is_not_resurrected(
    completion, delete
):
    from policyengine_core.periods import period as period_
    from policyengine_uk.model_api import BenUnit, Reform, Variable, YEAR

    class absent_slot_delete_probe(Variable):
        label = "Public absent-slot deletion probe"
        entity = BenUnit
        definition_period = YEAR
        value_type = float

        def formula(benunit, period):
            simulation = benunit.simulation
            equals(money(simulation, "child_benefit", 2027), [0])
            holder = simulation.get_holder("child_benefit")
            target = period_(2026)
            branch = simulation.branch_name
            # Prove this exact physical slot contains no genuine input before
            # arranging the original no-op-delete premise. Missing slots need
            # no derived mark; every present memory/disk slot must be derived.
            assert ("child_benefit", branch, target) not in simulation._user_input_keys
            assert holder._stores_user_input(target, branch) is False
            for storage in (holder._memory_storage, holder._disk_storage):
                if storage is not None:
                    present = storage.has(target, branch)
                    assert type(present) is bool
                    if present:
                        assert storage.is_derived(target, branch) is True
            simulation.drop_computed_arrays()
            # This is the actual physical absence that tuple-only tracking
            # misses: no input record and no array in either physical tier.
            assert not holder._memory_storage.has(target, branch)
            assert holder._disk_storage is None or not holder._disk_storage.has(
                target, branch
            )
            assert ("child_benefit", branch, target) not in simulation._user_input_keys
            if delete:
                holder.delete_arrays(target, branch_name=branch)
            if completion == "exception":
                raise ValueError("reported-mode absent-slot deletion probe")
            return np.zeros(benunit.count)

    class probe(Reform):
        def apply(self):
            self.add_variable(absent_slot_delete_probe)

    simulation = construct(
        changes={REPORTED_ONLY: {FY2026: True}}, dataset=reported_dataset()
    )
    simulation.apply_reform(probe)
    if completion == "exception":
        with pytest.raises(
            ValueError, match="^reported-mode absent-slot deletion probe$"
        ):
            simulation.calculate("absent_slot_delete_probe", 2027)
    else:
        equals(money(simulation, "absent_slot_delete_probe", 2027), [0])
    equals(money(simulation, "child_benefit", 2026), [0 if delete else 666])
    equals(money(simulation, "child_benefit", 2027), [0])
    key = ("child_benefit", simulation.branch_name, period_(2026))
    assert (key in simulation._user_input_keys) is (not delete)
    # Retire only the deleted slot; the unrelated declared report remains.
    equals(money(simulation, "esa_income", 2026), [600])


@pytest.mark.parametrize(
    "completion,action",
    (
        ("return", "delete"),
        ("exception", "delete"),
        ("return", "none"),
        ("exception", "none"),
        ("return", "genuine"),
        ("exception", "genuine"),
    ),
    ids=(
        "delete_return",
        "delete_exception",
        "control_return",
        "control_exception",
        "genuine_return",
        "genuine_exception",
    ),
)
def test_reported_mode_inactive_clone_delete_before_first_calculate(completion, action):
    from policyengine_core.periods import period as period_
    from policyengine_uk.model_api import BenUnit, Reform, Variable, YEAR

    created = []

    class inactive_clone_escape_probe(Variable):
        label = "Public inactive clone escape probe"
        entity = BenUnit
        definition_period = YEAR
        value_type = float

        def formula(benunit, period):
            parent = benunit.simulation
            equals(money(parent, "child_benefit", 2027), [0])
            target = period_(2026)
            physical_branch = parent.branch_name
            parent_holder = parent.get_holder("child_benefit")
            # Prove this exact physical slot contains no genuine input before
            # arranging the original no-op-delete premise. Missing slots need
            # no derived mark; every present memory/disk slot must be derived.
            assert (
                "child_benefit",
                physical_branch,
                target,
            ) not in parent._user_input_keys
            assert parent_holder._stores_user_input(target, physical_branch) is False
            for storage in (parent_holder._memory_storage, parent_holder._disk_storage):
                if storage is not None:
                    present = storage.has(target, physical_branch)
                    assert type(present) is bool
                    if present:
                        assert storage.is_derived(target, physical_branch) is True
            parent.drop_computed_arrays()
            assert not parent_holder._memory_storage.has(target, physical_branch)
            assert (
                parent_holder._disk_storage is None
                or not parent_holder._disk_storage.has(target, physical_branch)
            )
            clone = parent.clone()
            created.append((clone, physical_branch))
            # No clone.calculate call precedes this direct physical operation;
            # the clone has no own Core calculation frame here.
            holder = clone.get_holder("child_benefit")
            if action == "delete":
                holder.delete_arrays(target, branch_name=physical_branch)
            elif action == "genuine":
                holder.set_input(target, np.array([999.0]), branch_name=physical_branch)
            if completion == "exception":
                raise ValueError("reported-mode inactive clone escape probe")
            return np.zeros(benunit.count)

    class probe(Reform):
        def apply(self):
            self.add_variable(inactive_clone_escape_probe)

    parent = construct(
        changes={REPORTED_ONLY: {FY2026: True}}, dataset=reported_dataset()
    )
    parent.apply_reform(probe)
    if completion == "exception":
        with pytest.raises(
            ValueError, match="^reported-mode inactive clone escape probe$"
        ):
            parent.calculate("inactive_clone_escape_probe", 2027)
    else:
        equals(money(parent, "inactive_clone_escape_probe", 2027), [0])
    assert created
    clone, physical_branch = created[-1]
    expected = {"delete": 0, "none": 666, "genuine": 999}[action]
    equals(money(clone, "child_benefit", 2026), [expected])
    key = ("child_benefit", physical_branch, period_(2026))
    assert (key in clone._user_input_keys) is (action != "delete")
    equals(money(clone, "esa_income", 2026), [600])
    equals(money(parent, "child_benefit", 2026), [666])
    for item in (clone, parent):
        equals(money(item, "child_benefit", 2027), [0])


@pytest.mark.parametrize("target", ("self", "clone", "branch"))
@pytest.mark.parametrize("replay", ("variable", "noop", "failure_before_replay"))
def test_reported_owned_inputs_survive_public_reform_replay(target, replay):
    from policyengine_uk.model_api import BenUnit, Reform, Variable, YEAR

    class public_replay_probe(Variable):
        label = "Public reported-input replay probe"
        entity = BenUnit
        definition_period = YEAR
        value_type = float

        def formula(benunit, period):
            return np.zeros(benunit.count)

    class public_replay(Reform):
        def apply(self):
            if replay == "failure_before_replay":
                raise ValueError("public reform failed before cache replay")
            if replay == "variable":
                self.add_variable(public_replay_probe)

    parent = construct(
        changes={REPORTED_ONLY: {FY2026: True}}, dataset=reported_dataset()
    )
    simulation = (
        parent
        if target == "self"
        else parent.clone()
        if target == "clone"
        else parent.get_branch("reported_public_replay", clone_system=True)
    )
    equals(money(simulation, "child_benefit", 2026), [666])
    if replay == "failure_before_replay":
        with pytest.raises(
            ValueError, match="^public reform failed before cache replay$"
        ):
            simulation.apply_reform(public_replay)
    else:
        simulation.apply_reform(public_replay)
    equals(money(simulation, "child_benefit", 2027), [0])
    equals(money(simulation, "child_benefit", 2026), [666])
    equals(money(simulation, "esa_income", 2026), [600])
    equals(money(parent, "child_benefit", 2026), [666])
    if replay == "variable":
        equals(money(simulation, "public_replay_probe", 2027), [0])


@pytest.mark.parametrize("mutation", ("equal", "same_array", "new", "delete"))
def test_public_reform_replay_preserves_genuine_holder_write_or_delete(mutation):
    from policyengine_core.periods import period as period_
    from policyengine_uk.model_api import Reform

    parent = construct(
        changes={REPORTED_ONLY: {FY2026: True}}, dataset=reported_dataset()
    )
    simulation = parent.clone()
    holder = simulation.get_holder("child_benefit")
    target = period_(2026)
    if mutation == "delete":
        expected = 0
    else:
        value = (
            holder.get_array(target, simulation.branch_name)
            if mutation == "same_array"
            else np.array([999 if mutation == "new" else 666.0])
        )
        expected = 999 if mutation == "new" else 666

    class no_policy_change(Reform):
        def apply(self):
            if mutation == "delete":
                holder.delete_arrays(target, branch_name=simulation.branch_name)
            else:
                holder.set_input(target, value, branch_name=simulation.branch_name)

    simulation.apply_reform(no_policy_change)
    equals(money(simulation, "child_benefit", 2026), [expected])
    equals(money(simulation, "child_benefit", 2027), [0])
    equals(money(simulation, "esa_income", 2026), [600])
    equals(money(parent, "child_benefit", 2026), [666])
