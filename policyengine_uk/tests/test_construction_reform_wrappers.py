"""Construction-owned reform wrappers retain their reading until edited."""

import copy
from decimal import Decimal, ROUND_CEILING

import numpy as np
import pytest
from policyengine_core.reforms import Reform

from policyengine_uk import Simulation
from policyengine_uk.scenarios.uc_reform import UCHealthElementOverrideWarning
from policyengine_uk.utils.scenario import Scenario


pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

BASIC_RATE = "gov.hmrc.income_tax.rates.uk[0].rate"
YEARS = (2026, 2027, 2028)
SITUATION = {
    "people": {"person1": {"age": {year: 40 for year in YEARS}}},
    "benunits": {"benunit": {"members": ["person1"]}},
    "households": {"household": {"members": ["person1"]}},
}
A = {BASIC_RATE: {"2027-01-01.2027-12-31": 0.31}}
L = {BASIC_RATE: {"2027-01-01": 0.35}}
VAT = "gov.hmrc.vat.standard_rate"
PA = "gov.hmrc.income_tax.allowances.personal_allowance.amount"
CPI = "gov.economic_assumptions.yoy_growth.obr.consumer_price_index"
STATUTORY_CPI = "gov.economic_assumptions.yoy_growth.september_cpi_uprating"
FISCAL_A = {BASIC_RATE: {"2026-04-06.2027-04-05": 0.31}}


def parameter(simulation, path, date):
    return simulation.tax_benefit_system.parameters.get_child(path)(date)


@pytest.mark.parametrize("before_data_load", [False, True])
@pytest.mark.parametrize("edit", ["legacy", "direct"])
@pytest.mark.parametrize("composite", [False, True])
def test_equal_constructor_wrapper_after_edit_matches_apply(
    before_data_load, edit, composite
):
    def build(use_apply):
        def wrapper(simulation):
            if edit == "legacy":
                Scenario.from_reform(L).apply(simulation)
            else:
                simulation.tax_benefit_system.parameters.get_child(BASIC_RATE).update(
                    period="2027", value=0.40
                )
                simulation.tax_benefit_system.reset_parameter_caches()
            requested = Scenario.from_reform((L, A) if composite else A)
            if use_apply:
                requested.apply(simulation)
            else:
                requested.simulation_modifier(simulation)

        own = Scenario.from_reform(A)
        own.applied_before_data_load = before_data_load
        return Simulation(
            situation=SITUATION,
            scenario=own
            + Scenario(
                simulation_modifier=wrapper,
                applied_before_data_load=before_data_load,
            ),
        )

    direct, applied = build(False), build(True)
    assert parameter(applied, BASIC_RATE, "2027-01-01") == 0.31
    assert parameter(direct, BASIC_RATE, "2027-01-01") == 0.31
    for date in ("2026-12-31", "2027-01-01", "2027-07-01", "2027-12-31", "2028-01-01"):
        assert parameter(direct, BASIC_RATE, date) == parameter(
            applied, BASIC_RATE, date
        )


@pytest.mark.parametrize("before_data_load", [False, True])
@pytest.mark.parametrize("deepcopy", [False, True])
@pytest.mark.parametrize("reform_class", [False, True])
def test_disjoint_composer_member_wrappers_keep_constructor_reading(
    before_data_load, deepcopy, reform_class
):
    # The acquired scenario_composition/v1 contract: all dated changes first,
    # followed by every member's modifier, including fresh equal member calls.
    reforms = (FISCAL_A, {VAT: {"2027-01-01.2027-12-31": 0.27}})
    members = [Scenario.from_reform(r) for r in reforms]

    def wrapper(simulation):
        for reform in reforms:
            request = Reform.from_dict(reform) if reform_class else reform
            Scenario.from_reform(request).simulation_modifier(simulation)

    if reform_class:
        members = [Scenario.from_reform(Reform.from_dict(r)) for r in reforms]
    scenario = Scenario(
        dated_reforms=[d for member in members for d in member.dated_reforms],
        simulation_modifier=wrapper,
        applied_before_data_load=before_data_load,
    )
    if deepcopy:
        scenario = copy.deepcopy(scenario)
    simulation = Simulation(situation=SITUATION, scenario=scenario)
    assert parameter(simulation, BASIC_RATE, "2026-01-01") == 0.31
    assert parameter(simulation, BASIC_RATE, "2027-01-01") == 0.20
    assert parameter(simulation, VAT, "2027-01-01") == 0.27
    assert simulation.tax_benefit_system.legacy_overrides == []
    assert simulation._construction_reform_state is None
    assert simulation.baseline._construction_reform_state is None


@pytest.mark.parametrize("before_data_load", [False, True])
@pytest.mark.parametrize("deepcopy", [False, True])
def test_pristine_mixed_own_wrapper_keeps_legacy_and_statutory_readings(
    before_data_load, deepcopy
):
    changes = {**FISCAL_A, VAT: {"2027-01-01": 0.27}}

    def wrapper(simulation):
        Scenario.from_reform(changes).simulation_modifier(simulation)

    scenario = Scenario.from_reform(changes)
    scenario.applied_before_data_load = before_data_load
    scenario += Scenario(
        simulation_modifier=wrapper, applied_before_data_load=before_data_load
    )
    if deepcopy:
        scenario = copy.deepcopy(scenario)
    simulation = Simulation(situation=SITUATION, scenario=scenario)
    assert parameter(simulation, BASIC_RATE, "2026-01-01") == 0.31
    assert parameter(simulation, BASIC_RATE, "2027-01-01") == 0.20
    assert parameter(simulation, VAT, "2027-01-01") == 0.27
    assert parameter(simulation, VAT, "2027-01-02") == 0.20


@pytest.mark.parametrize("before_data_load", [False, True])
def test_unrelated_direct_edit_does_not_replay_own_fiscal_change(before_data_load):
    def wrapper(simulation):
        simulation.tax_benefit_system.parameters.get_child(VAT).update(
            period="2027", value=0.40
        )
        simulation.tax_benefit_system.reset_parameter_caches()
        Scenario.from_reform(FISCAL_A).simulation_modifier(simulation)

    scenario = Scenario.from_reform(FISCAL_A)
    scenario.applied_before_data_load = before_data_load
    simulation = Simulation(
        situation=SITUATION,
        scenario=scenario
        + Scenario(
            simulation_modifier=wrapper, applied_before_data_load=before_data_load
        ),
    )
    assert parameter(simulation, BASIC_RATE, "2026-01-01") == 0.31
    assert parameter(simulation, BASIC_RATE, "2027-01-01") == 0.20
    assert parameter(simulation, VAT, "2027-01-01") == 0.40
    assert simulation.tax_benefit_system.legacy_overrides == []


@pytest.mark.parametrize("edit", ["legacy", "direct"])
def test_foreign_edit_survives_phase_boundary_as_foreign(edit):
    def before(simulation):
        if edit == "legacy":
            Scenario.from_reform(L).apply(simulation)
        else:
            simulation.tax_benefit_system.parameters.get_child(BASIC_RATE).update(
                period="2027", value=0.40
            )
            simulation.tax_benefit_system.reset_parameter_caches()

    def after(simulation):
        Scenario.from_reform(A).simulation_modifier(simulation)

    scenario = Scenario.from_reform(A)
    scenario.applied_before_data_load = True
    scenario += Scenario(simulation_modifier=before, applied_before_data_load=True)
    scenario += Scenario(simulation_modifier=after)
    simulation = Simulation(situation=SITUATION, scenario=scenario)
    assert parameter(simulation, BASIC_RATE, "2027-01-01") == 0.31


@pytest.mark.parametrize("before_data_load", [False, True])
def test_direct_edit_outside_window_still_disables_construction_privilege(
    before_data_load,
):
    def wrapper(simulation):
        simulation.tax_benefit_system.parameters.get_child(BASIC_RATE).update(
            period="2030", value=0.40
        )
        simulation.tax_benefit_system.reset_parameter_caches()
        Scenario.from_reform(FISCAL_A).simulation_modifier(simulation)

    scenario = Scenario.from_reform(FISCAL_A)
    scenario.applied_before_data_load = before_data_load
    simulation = Simulation(
        situation=SITUATION,
        scenario=scenario
        + Scenario(
            simulation_modifier=wrapper, applied_before_data_load=before_data_load
        ),
    )
    # A direct edit has no write-log record. Even an edit outside A's dates
    # ends its path's construction privilege: A now takes the built reading.
    assert parameter(simulation, BASIC_RATE, "2027-01-01") == 0.31
    assert parameter(simulation, BASIC_RATE, "2030-01-01") == 0.40


@pytest.mark.parametrize("before_data_load", [False, True])
@pytest.mark.parametrize("deepcopy", [False, True])
def test_pristine_equal_member_keeps_constructor_later_member_order(
    before_data_load, deepcopy
):
    later = {BASIC_RATE: {"2027-01-01.2027-12-31": 0.35}}

    def wrapper(simulation):
        Scenario.from_reform(A).simulation_modifier(simulation)

    scenario = Scenario.from_reform((A, later))
    scenario.applied_before_data_load = before_data_load
    scenario += Scenario(
        simulation_modifier=wrapper, applied_before_data_load=before_data_load
    )
    if deepcopy:
        scenario = copy.deepcopy(scenario)
    simulation = Simulation(situation=SITUATION, scenario=scenario)
    assert parameter(simulation, BASIC_RATE, "2027-01-01") == 0.35
    assert simulation.tax_benefit_system.legacy_overrides == []


@pytest.mark.parametrize("before_data_load", [False, True])
def test_original_lcwra_shadow_is_not_a_foreign_parameter_edit(before_data_load):
    situation = copy.deepcopy(SITUATION)
    situation["people"]["person1"]["uc_limited_capability_for_WRA"] = {
        year: True for year in YEARS
    }
    situation["benunits"]["benunit"].update(
        would_claim_uc={year: True for year in YEARS},
        uc_receives_new_claimant_health_element={year: False for year in YEARS},
    )
    path = "gov.dwp.universal_credit.elements.disabled.amount"
    changes = {path: {"2026-01-01.2028-12-31": 999.0}}
    own = Scenario.from_reform(changes)
    own.applied_before_data_load = before_data_load
    with pytest.warns(UCHealthElementOverrideWarning):
        control = Simulation(situation=situation, scenario=own)

    def wrapper(simulation):
        Scenario.from_reform(changes).simulation_modifier(simulation)

    with pytest.warns(UCHealthElementOverrideWarning) as recorded:
        simulation = Simulation(
            situation=situation,
            scenario=own
            + Scenario(
                simulation_modifier=wrapper,
                applied_before_data_load=before_data_load,
            ),
        )
    assert len(recorded) == 1
    assert parameter(simulation, path, "2027-01-01") == 999.0
    expected = control.calculate("uc_LCWRA_element", 2027)
    assert np.all((expected > 0) & (expected < 999.0 * 12))
    np.testing.assert_array_equal(
        simulation.calculate("uc_LCWRA_element", 2027), expected
    )
    assert simulation.tax_benefit_system.legacy_overrides == []


class ScaleAllowance(Reform):
    def apply(self):
        target = self.parameters.get_child(PA)
        target.update(period="2027", value=target("2027") * 1.1)


def scale_allowance(simulation):
    target = simulation.tax_benefit_system.parameters.get_child(PA)
    target.update(period="2027", value=target("2027") * 1.1)
    simulation.tax_benefit_system.reset_parameter_caches()


@pytest.mark.parametrize("copy_kind", ["clone", "branch"])
@pytest.mark.parametrize("representation", ["class", "modifier", "cpi_dict"])
def test_relative_reforms_on_copies_match_explicit_apply(copy_kind, representation):
    if representation == "class":
        scenario = Scenario.from_reform(ScaleAllowance)
    elif representation == "modifier":
        scenario = Scenario(simulation_modifier=scale_allowance)
    else:
        scenario = Scenario.from_reform({CPI: {"2027": 0.08}})
    original = Simulation(situation=SITUATION)
    original_allowance = parameter(original, PA, "2027")
    original_cpi = parameter(original, CPI, "2027")
    direct = (
        original.clone()
        if copy_kind == "clone"
        else original.get_branch("copy", clone_system=True)
    )
    applied = original.clone()
    scenario.simulation_modifier(direct)
    scenario.apply(applied)
    for path in (PA, CPI):
        for year in YEARS:
            assert parameter(direct, path, str(year)) == parameter(
                applied, path, str(year)
            )
    if representation == "cpi_dict":
        assert parameter(direct, CPI, "2027") == 0.08
    else:
        assert parameter(direct, PA, "2027") == pytest.approx(original_allowance * 1.1)
    assert parameter(original, PA, "2027") == original_allowance
    assert parameter(original, CPI, "2027") == original_cpi


@pytest.mark.parametrize("copy_kind", ["clone", "branch"])
def test_mixed_replay_on_copy_changes_its_own_construction_reading(copy_kind):
    changes = {
        BASIC_RATE: {"2026-06-01.2027-03-31": 0.31},
        VAT: {"2027-01-01": 0.25},
    }
    original = Simulation(situation=SITUATION, reform=changes)
    assert parameter(original, BASIC_RATE, "2027-01-01") == 0.20
    simulation = (
        original.clone()
        if copy_kind == "clone"
        else original.get_branch("copy", clone_system=True)
    )
    Scenario.from_reform(changes).simulation_modifier(simulation)
    assert parameter(simulation, BASIC_RATE, "2027-01-01") == 0.31
    assert parameter(simulation, VAT, "2027-01-01") == 0.25
    assert parameter(original, BASIC_RATE, "2027-01-01") == 0.20


def test_indexed_freeze_needs_construction_for_indexation_resume():
    changes = {PA: {"2026-04-06.2033-04-05": 12_570}}
    constructed = Simulation(situation=SITUATION, reform=changes)
    built = Simulation(situation=SITUATION)
    baseline_2034 = parameter(built, PA, "2034")
    Scenario.from_reform(changes).apply(built)
    increase = Decimal(str(parameter(constructed, STATUTORY_CPI, "2033")))
    expected = float(
        (Decimal(12_570) * (1 + increase) / 10).to_integral_value(
            rounding=ROUND_CEILING
        )
        * 10
    )
    assert parameter(constructed, PA, "2033") == expected
    assert parameter(built, PA, "2033") == 12_570
    assert parameter(built, PA, "2034") == baseline_2034
