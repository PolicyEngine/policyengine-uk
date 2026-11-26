"""Missing take-up inputs are diagnosed without changing calculator defaults.

Issue #2916 defines a variable-level diagnostic, not a calibration or per-year
completeness check. All datasets here are synthetic, with one adult per family.
"""

import re
import warnings

import numpy as np
import pandas as pd
import pytest
from policyengine_core.periods import period

from policyengine_uk import Microsimulation, Simulation
from policyengine_uk.data import UKMultiYearDataset, UKSingleYearDataset
from policyengine_uk.model_api import MONTH, YEAR, BenUnit, Person, Scenario, Variable


pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
YEAR_VALUE = 2025


def single_year(
    year=YEAR_VALUE, *, person_inputs=None, benunit_inputs=None, household_inputs=None
):
    return UKSingleYearDataset(
        person=pd.DataFrame(
            {
                "person_id": [1],
                "person_benunit_id": [1],
                "person_household_id": [1],
                "age": [35],
                "employment_income": [20_000.0],
                **(person_inputs or {}),
            }
        ),
        benunit=pd.DataFrame({"benunit_id": [1], **(benunit_inputs or {})}),
        household=pd.DataFrame(
            {
                "household_id": [1],
                "household_weight": [1.0],
                "region": ["LONDON"],
                "tenure_type": ["OWNED_OUTRIGHT"],
                "rent": [0.0],
                "council_tax": [0.0],
                **(household_inputs or {}),
            }
        ),
        fiscal_year=year,
    )


def data(**kwargs):
    # Explicit multi-year data avoids testing projection in every warning case.
    return UKMultiYearDataset(datasets=[single_year(**kwargs)])


def takeup_warnings(caught):
    return [
        item
        for item in caught
        if issubclass(item.category, UserWarning)
        and "would_claim_" in str(item.message)
    ]


def warned_names(item):
    return set(re.findall(r"\bwould_claim_[a-z0-9_]+\b", str(item.message)))


def capture_build(**kwargs):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        simulation = Microsimulation(**kwargs)
    return simulation, takeup_warnings(caught)


def test_single_year_dataset_emits_one_aggregated_named_warning():
    _, caught = capture_build(dataset=single_year())

    assert len(caught) == 1
    assert caught[0].category is UserWarning
    assert {
        "would_claim_uc",
        "would_claim_pc",
        "would_claim_uc_childcare",
        "would_claim_carers_allowance",
    } <= warned_names(caught[0])
    assert "would_claim_student_loan" not in warned_names(caught[0])
    assert "warn_on_missing_takeup_inputs=False" in str(caught[0].message)
    assert caught[0].filename == __file__


@pytest.mark.parametrize(
    "value", [True, False], ids=["explicit-true", "explicit-false"]
)
def test_supplied_claim_input_is_omitted_regardless_of_its_value(value):
    simulation, caught = capture_build(
        dataset=data(benunit_inputs={"would_claim_uc": [value]})
    )

    assert len(caught) == 1
    assert "would_claim_uc" not in warned_names(caught[0])
    assert "would_claim_pc" in warned_names(caught[0])
    np.testing.assert_array_equal(
        simulation.calculate("would_claim_uc", YEAR_VALUE), [value]
    )


def test_opt_out_suppresses_only_the_diagnostic():
    simulation, caught = capture_build(
        dataset=data(), warn_on_missing_takeup_inputs=False
    )

    assert caught == []
    np.testing.assert_array_equal(
        simulation.calculate("would_claim_uc", YEAR_VALUE), [True]
    )


def test_explicit_inputs_for_all_claim_flags_are_quiet():
    # Supply every prefixed variable, including irrelevant false/formula defaults.
    # This does not duplicate the production diagnostic's qualification predicate.
    reference = Simulation(situation={"age": {YEAR_VALUE: 35}})
    tables = {"person": {}, "benunit": {}, "household": {}}
    for name, variable in reference.tax_benefit_system.variables.items():
        if name.startswith("would_claim_"):
            tables[variable.entity.key][name] = [False]
    assert "would_claim_uc" in tables["benunit"]
    _, caught = capture_build(
        dataset=data(
            person_inputs=tables["person"],
            benunit_inputs=tables["benunit"],
            household_inputs=tables["household"],
        )
    )

    assert caught == []


@pytest.mark.parametrize("simulation_class", [Simulation, Microsimulation])
def test_household_situations_remain_quiet(simulation_class):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        simulation = simulation_class(situation={"age": {YEAR_VALUE: 35}})

    assert takeup_warnings(caught) == []
    np.testing.assert_array_equal(
        simulation.calculate("would_claim_uc", YEAR_VALUE), [True]
    )


def test_plain_simulation_built_from_data_remains_quiet():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        Simulation(dataset=data())

    assert takeup_warnings(caught) == []


def test_scenario_overrides_are_supplied_before_the_single_warning():
    def supply(simulation):
        simulation.set_input("would_claim_uc", YEAR_VALUE, [False])

    simulation, caught = capture_build(
        dataset=data(), scenario=Scenario(simulation_modifier=supply)
    )

    assert len(caught) == 1
    assert "would_claim_uc" not in warned_names(caught[0])
    assert "would_claim_pc" in warned_names(caught[0])
    np.testing.assert_array_equal(
        simulation.calculate("would_claim_uc", YEAR_VALUE), [False]
    )
    np.testing.assert_array_equal(
        simulation.baseline.calculate("would_claim_uc", YEAR_VALUE), [True]
    )


def test_clone_branch_and_calculations_do_not_repeat_the_warning():
    simulation, caught = capture_build(dataset=data())
    assert len(caught) == 1

    with warnings.catch_warnings(record=True) as later:
        warnings.simplefilter("always")
        for copy in (simulation.clone(), simulation.get_branch()):
            np.testing.assert_array_equal(
                copy.calculate("would_claim_uc", YEAR_VALUE), [True]
            )

    assert takeup_warnings(later) == []


def test_one_supplied_period_is_enough_in_a_sparse_multiyear_dataset():
    source = UKMultiYearDataset(
        datasets=[
            single_year(benunit_inputs={"would_claim_uc": [False]}),
            single_year(YEAR_VALUE + 1),
        ]
    )
    simulation, caught = capture_build(dataset=source)

    assert len(caught) == 1
    assert "would_claim_uc" not in warned_names(caught[0])
    assert "would_claim_pc" in warned_names(caught[0])
    np.testing.assert_array_equal(
        simulation.calculate("would_claim_uc", YEAR_VALUE), [False]
    )


def install_probe_variables(simulation):
    """Independent cases distinguish names, types, defaults and final formulas."""

    class would_claim_future_flag(Variable):
        label = "Synthetic future take-up input"
        value_type = bool
        entity = BenUnit
        definition_period = YEAR
        default_value = True

    class would_claim_false_probe(Variable):
        label = "Synthetic take-up input with a false default"
        value_type = bool
        entity = BenUnit
        definition_period = YEAR
        default_value = False

    class would_claim_formula_probe(Variable):
        label = "Synthetic formula-backed take-up flag"
        value_type = bool
        entity = BenUnit
        definition_period = YEAR
        default_value = True

        def formula(benunit, period, parameters):
            return True

    class would_claim_number_probe(Variable):
        label = "Synthetic numeric prefixed input"
        value_type = int
        entity = BenUnit
        definition_period = YEAR
        default_value = 1

    class unrelated_true_probe(Variable):
        label = "Synthetic unrelated true-default input"
        value_type = bool
        entity = BenUnit
        definition_period = YEAR
        default_value = True

    class would_claim_neutralized_probe(Variable):
        label = "Synthetic neutralized take-up input"
        value_type = bool
        entity = BenUnit
        definition_period = YEAR
        default_value = True

    for definition in (
        would_claim_future_flag,
        would_claim_false_probe,
        would_claim_formula_probe,
        would_claim_number_probe,
        unrelated_true_probe,
        would_claim_neutralized_probe,
    ):
        simulation.tax_benefit_system.add_variable(definition)
    simulation.tax_benefit_system.neutralize_variable("would_claim_neutralized_probe")
    simulation.tax_benefit_system.neutralize_variable("would_claim_pc")


def test_final_registry_discovers_new_flags_and_excludes_inapplicable_definitions():
    _, caught = capture_build(
        dataset=data(),
        scenario=Scenario(
            simulation_modifier=install_probe_variables, applied_before_data_load=True
        ),
    )

    assert len(caught) == 1
    names = warned_names(caught[0])
    assert {"would_claim_future_flag", "would_claim_uc"} <= names
    assert not names & {
        "would_claim_false_probe",
        "would_claim_formula_probe",
        "would_claim_number_probe",
        "would_claim_neutralized_probe",
        "would_claim_pc",
    }
    assert "unrelated_true_probe" not in str(caught[0].message)


def test_dataframe_monthly_input_replay_counts_as_supplied():
    class would_claim_monthly_probe(Variable):
        label = "Synthetic monthly take-up input"
        value_type = bool
        entity = Person
        definition_period = MONTH
        default_value = True

    def install(simulation):
        simulation.tax_benefit_system.add_variable(would_claim_monthly_probe)

    frame = pd.DataFrame(
        {
            f"person_id__{YEAR_VALUE}": [1],
            f"person_benunit_id__{YEAR_VALUE}": [1],
            f"person_household_id__{YEAR_VALUE}": [1],
            f"benunit_id__{YEAR_VALUE}": [1],
            f"household_id__{YEAR_VALUE}": [1],
            f"household_weight__{YEAR_VALUE}": [1.0],
            f"age__{YEAR_VALUE}": [35],
            f"would_claim_monthly_probe__{YEAR_VALUE}-07": [False],
        }
    )
    simulation, caught = capture_build(
        dataset=frame,
        scenario=Scenario(simulation_modifier=install, applied_before_data_load=True),
    )

    assert len(caught) == 1
    assert "would_claim_monthly_probe" not in warned_names(caught[0])
    assert "would_claim_uc" in warned_names(caught[0])
    np.testing.assert_array_equal(
        simulation.calculate("would_claim_monthly_probe", f"{YEAR_VALUE}-07"), [False]
    )


@pytest.mark.parametrize("cache_kind", ["default", "derived"])
def test_cached_values_do_not_conceal_missing_inputs(monkeypatch, cache_kind):
    original_init = Simulation.__init__

    def build_then_cache(simulation, *args, **kwargs):
        original_init(simulation, *args, **kwargs)
        if isinstance(simulation, Microsimulation):
            if cache_kind == "default":
                simulation.calculate("would_claim_uc", YEAR_VALUE)
            else:
                simulation.get_holder("would_claim_uc").put_in_cache(
                    np.array([False]), period(YEAR_VALUE), derived=True
                )

    # Install a cache after normal parent construction, before the public
    # Microsimulation constructor returns and emits its diagnostic.
    monkeypatch.setattr(Simulation, "__init__", build_then_cache)
    _, caught = capture_build(dataset=data())

    assert len(caught) == 1
    assert "would_claim_uc" in warned_names(caught[0])


def test_warning_toggle_preserves_inputs_and_representative_outputs():
    source = data(benunit_inputs={"would_claim_uc": [False]})
    enabled, caught = capture_build(dataset=source)
    disabled, quiet = capture_build(dataset=source, warn_on_missing_takeup_inputs=False)
    assert len(caught) == 1
    assert quiet == []

    for name in (
        "would_claim_uc",
        "would_claim_pc",
        "employment_income",
        "income_tax",
        "universal_credit",
        "household_net_income",
    ):
        np.testing.assert_array_equal(
            enabled.calculate(name, YEAR_VALUE), disabled.calculate(name, YEAR_VALUE)
        )
    assert source[YEAR_VALUE].benunit["would_claim_uc"].tolist() == [False]
    assert source[YEAR_VALUE].person["employment_income"].tolist() == [20_000.0]
