from .cps.marriage_tax_reforms import create_period_aware_marriage_tax_reform
from .conservatives.household_based_hitc import (
    create_period_aware_household_hitc_reform,
)
from .policyengine import (
    disable_simulated_benefits,
)
from .policyengine.adjust_budgets import adjust_budgets
from .scotland.scottish_child_payment_reform import (
    create_period_aware_scottish_child_payment_reform,
)
from policyengine_core.model_api import *
from policyengine_core import periods


def create_structural_reforms_from_parameters(parameters, period):
    period = periods.period(period)
    reforms = [
        create_period_aware_marriage_tax_reform(parameters, period),
        create_period_aware_household_hitc_reform(parameters, period),
        disable_simulated_benefits(parameters, period, _period_aware=True),
        adjust_budgets(parameters, period),
        create_period_aware_scottish_child_payment_reform(parameters, period),
    ]
    reforms = tuple(filter(lambda x: x is not None, reforms))

    class combined_reform(Reform):
        def apply(self):
            for reform in reforms:
                reform.apply(self)

    return combined_reform


def finite_parameter_activation(leaves, predicate):
    """Inspect actual effective points, including raw early-year sentinels.

    Sampling starts only where every participating leaf has history. A missing
    or null value there is unsupported, rather than an implicit off switch.
    """
    histories = [leaf.values_list for leaf in leaves]
    if any(not history for history in histories):
        raise ValueError("Structural reform parameters require effective history")
    first_covered = max(
        min(value.instant_str for value in history) for history in histories
    )
    points = sorted({value.instant_str for history in histories for value in history})
    available = False
    for point in points:
        if point < first_covered:
            continue
        # Parameter._get_at_instant accepts the stored string directly. The
        # public callable would try to turn year 0000 into a datetime.date.
        values = [leaf._get_at_instant(point) for leaf in leaves]
        if any(value is None for value in values):
            raise ValueError(f"Structural reform parameter has no value at {point}")
        # Validate later points even after an earlier interval is active.
        # An explicit null anywhere in covered history remains unsupported.
        active_at_point = bool(predicate(values))
        available = active_at_point or available
    return available


def parameter_ever_true(parameters, path):
    return finite_parameter_activation(
        [parameters.get_child(path)], lambda values: bool(values[0])
    )


def apply_period_aware_reform(system, reform, names, active):
    """Route each replacement through the original dated Variable API.

    The contributed and original definitions must share storage and masking
    metadata. Formula execution, including adds/subtracts, stays in Core.
    """
    originals = {name: system.variables[name].clone() for name in names}
    trial = system.clone()
    reform.apply(trial)
    metadata = (
        "value_type",
        "definition_period",
        "default_value",
        "defined_for",
        "end",
        "set_input",
        "calculate_output",
        "uprating",
    )
    for name, original in originals.items():
        replacement = trial.variables[name]
        if original.entity.key != replacement.entity.key or any(
            getattr(original, key, None) != getattr(replacement, key, None)
            for key in metadata
        ):
            raise ValueError(f"Structural reform changes routing metadata for {name}")
    reform.apply(system)
    for name, original in originals.items():
        replacement = system.variables[name].clone()
        routed = replacement.clone()

        def route(original, replacement):
            def formula(population, period, parameters):
                simulation = population.simulation
                root = simulation.tax_benefit_system.parameters
                selected = replacement if active(root, period) else original
                return simulation._run_formula(selected, population, period)

            return formula

        starts = set(original.formulas) | set(replacement.formulas)
        if not starts:
            raise ValueError(f"Structural reform has no formula route for {name}")
        routed.formulas.clear()
        routed.formulas[min(starts)] = route(original, replacement)
        system.variables[name] = routed
