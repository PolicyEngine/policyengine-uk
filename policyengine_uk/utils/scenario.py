import logging

from pydantic import BaseModel, ConfigDict
from typing import Any, Literal, List, Optional, Callable, Dict, Type, Union
from policyengine_core.simulations import Simulation
from policyengine_core.reforms import Reform
from policyengine_uk.utils.dated_reforms import (
    ALL_PERIODS,
    REFORM_DICT,
    REFORM_FROM_DICT,
    LegacyOverride,
    ParameterAssignment,
    apply_legacy_overrides,
    read_reform_dict,
    read_reform_from_dict,
)
from policyengine_uk.utils.parameters import check_parameter_not_removed

logger = logging.getLogger(__name__)

# Set on a simulation while Scenario.apply runs its modifier.
APPLYING_TO_BUILT_SIMULATION = "_scenario_apply_to_built_simulation"


class DatedReform(BaseModel):
    """A parameter reform dict and the route whose key reading it takes.

    ``reading`` is ``"reform_dict"`` for a dict passed as a reform and
    ``"reform_from_dict"`` for the dict behind a policyengine-core
    ``Reform.from_dict`` class. See ``policyengine_uk.utils.dated_reforms``.
    """

    reading: Literal["reform_dict", "reform_from_dict"]
    changes: Dict[str, Any]

    def read(
        self,
        defines,
        order_start: int = 0,
        warn: bool = False,
        calendar_years=None,
    ):
        if self.reading == REFORM_DICT:
            return read_reform_dict(
                self.changes,
                defines,
                order_start,
                warn=warn,
                calendar_years=calendar_years,
            )
        return read_reform_from_dict(self.changes, defines, order_start)


def _canonical_paths(changes: Dict[str, Any]) -> Dict[str, Any]:
    """Changes keyed by canonical parameter paths.

    A deprecated labour supply alias path names the parameter it copies,
    which is the one formulas read.
    """
    from policyengine_uk.parameters.gov.simulation.labour_supply_responses.aliases import (
        canonicalize_lsr_parameter_path,
    )

    return {
        canonicalize_lsr_parameter_path(path): value for path, value in changes.items()
    }


def _is_reform_from_dict(reform: Type[Reform]) -> bool:
    """Whether a Reform class was built by ``Reform.from_dict``."""
    return reform.__qualname__ == "Reform.from_dict.<locals>.reform" and isinstance(
        getattr(reform, "parameter_values", None), dict
    )


def _legacy_override_modifier(dated: DatedReform) -> Callable[[Simulation], None]:
    """Apply what a dated reform leaves to the annualised parameters.

    That is single-day or single-month reform-dict keys and paths the
    statutory tree does not define, such as a parameter a structural reform
    in the same tuple adds. The simulation applies the rest from the
    statutory timeline before any modifier runs.
    """

    def modifier(simulation: Simulation) -> None:
        from policyengine_uk.tax_benefit_system import (
            parameter_reads_calendar_years,
            reform_parameter_defines,
        )

        # Scenario.apply edits an already-built simulation's annualised
        # parameters, so there every change of the reform is an override.
        every_change = getattr(simulation, APPLYING_TO_BUILT_SIMULATION, False)
        defines = (lambda path: False) if every_change else reform_parameter_defines()
        _, legacy = dated.read(
            defines,
            warn=not every_change,
            calendar_years=parameter_reads_calendar_years(),
        )
        if not legacy:
            return
        _add_overrides(simulation, legacy)

    return modifier


def _add_overrides(simulation: Simulation, overrides: List[LegacyOverride]) -> None:
    system = simulation.tax_benefit_system
    if hasattr(system, "add_legacy_overrides"):
        # Kept by the system, so a later rebuild applies them again.
        system.add_legacy_overrides(overrides)
    else:
        apply_legacy_overrides(system.parameters, overrides)
        system.reset_parameter_caches()
    if getattr(simulation, "populations", None) is not None:
        simulation._invalidate_all_caches()


def _apply_reform_class(reform: Type[Reform], simulation: Simulation) -> None:
    """Apply a structural ``Reform`` class to a simulation's own system.

    policyengine-core's ``Reform.__init__`` takes a baseline system and
    builds a separate reformed system, so a simulation instead runs the
    class's ``apply`` on its own tax-benefit system, as
    ``Simulation.apply_reform`` does. Before data load there are no
    populations or cached values, so only the system changes; afterwards
    ``Simulation.apply_reform`` also discards cached formula output.
    """
    # A modifier cannot know its phase when the Scenario is built, because
    # ``applied_before_data_load`` is set on the Scenario afterwards, so the
    # simulation's populations (created by data load) are the phase signal.
    if getattr(simulation, "populations", None) is None:
        reform.apply(simulation.tax_benefit_system)
    else:
        simulation.apply_reform(reform)
    # Adding or replacing parameter nodes does not clear the per-node
    # at-instant caches the way ``Parameter.update`` does.
    simulation.tax_benefit_system.reset_parameter_caches()


class Scenario(BaseModel):
    """Represents a scenario configuration for policy simulations.

    A scenario can include parameter changes and/or simulation modifications
    that are applied before running a simulation. Scenarios can be combined
    using the + operator.
    """

    applied_before_data_load: bool = False

    parameter_changes: Optional[
        Dict[
            str,
            Union[
                int,
                float,
                bool,
                Dict[Union[str, int], Union[int, float, bool]],
            ],
        ]
    ] = None
    """A dictionary of parameter changes to apply to the simulation. These are applied *before* parameter operations."""

    dated_reforms: Optional[List[DatedReform]] = None
    """Reform dicts written onto the statutory timeline, in order, after ``parameter_changes``. ``Scenario.from_reform`` builds these from a dict or a ``Reform.from_dict`` class."""

    simulation_modifier: Optional[Callable[["Simulation"], None]] = None
    """A function that modifies the simulation before running it."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __add__(self, other: "Scenario") -> "Scenario":
        """Combine two scenarios by merging parameter changes and chaining modifiers.

        Args:
            other: Another Scenario to combine with this one

        Returns:
            A new Scenario with merged parameter changes and combined modifiers
        """
        # Merge parameter changes (other's changes take precedence in conflicts)
        merged_params = {}

        if self.parameter_changes:
            merged_params.update(self.parameter_changes)

        if other.parameter_changes:
            for key, value in other.parameter_changes.items():
                if (
                    key in merged_params
                    and isinstance(merged_params[key], dict)
                    and isinstance(value, dict)
                ):
                    # Deep merge nested dictionaries
                    merged_params[key] = {**merged_params[key], **value}
                else:
                    # Simple override
                    merged_params[key] = value

        # Chain simulation modifiers
        combined_modifier = None

        if self.simulation_modifier and other.simulation_modifier:
            # Both have modifiers - chain them
            def combined_modifier(simulation: Simulation) -> None:
                self.simulation_modifier(simulation)
                other.simulation_modifier(simulation)

        elif self.simulation_modifier:
            combined_modifier = self.simulation_modifier
        elif other.simulation_modifier:
            combined_modifier = other.simulation_modifier

        dated_reforms = (self.dated_reforms or []) + (other.dated_reforms or [])

        # Return new scenario with merged configuration
        return Scenario(
            parameter_changes=merged_params if merged_params else None,
            dated_reforms=dated_reforms or None,
            simulation_modifier=combined_modifier,
        )

    def dated_assignments(self, order_start: int = 0) -> List[ParameterAssignment]:
        """The statutory-timeline changes of ``dated_reforms``, in order."""
        from policyengine_uk.tax_benefit_system import (
            parameter_reads_calendar_years,
            reform_parameter_defines,
        )

        defines = reform_parameter_defines()
        calendar_years = parameter_reads_calendar_years()
        assignments: List[ParameterAssignment] = []
        for dated in self.dated_reforms or []:
            read, _ = dated.read(
                defines,
                order_start + len(assignments),
                calendar_years=calendar_years,
            )
            assignments += read
        return assignments

    @classmethod
    def from_reform(cls, reform: Union[tuple, dict, Type[Reform]]) -> "Scenario":
        """Create a Scenario from various reform representations.

        Args:
            reform: Can be:
                - A Reform class, including one built by ``Reform.from_dict``
                  or ``set_parameter``, applied to the simulation's own
                  tax-benefit system as ``Simulation.apply_reform`` does
                - A dict of parameter changes
                - A tuple of any of these (nested tuples allowed), applied
                  in order

        A dict, or the dict behind a ``Reform.from_dict`` class, is written
        onto the statutory timeline and the parameters are processed as
        current law is, so a change dated 6 April sets that fiscal year and
        derived parameters (uprating, the indexed thresholds) follow it. Each
        keeps its reading of period keys, including inside a tuple: in a
        dict, a bare-year key such as ``"2026"`` changes that fiscal year
        only, a single-day key overrides the annualised parameter on that
        day only, and a scalar value applies from 2023. ``Reform.from_dict``
        reads a bare year or a date as that instant onwards. The two agree
        for ``"YYYY-MM-DD.YYYY-MM-DD"`` keys. See
        ``policyengine_uk.utils.dated_reforms``.

        Returns:
            A new Scenario configured with the reform

        Raises:
            ValueError: If reform type is not supported, including a Reform
                instance (whose own state would be lost, since the reform is
                applied to the simulation's system through its class) and the
                removed ``(reform_class, *args)`` tuple form
        """
        if isinstance(reform, Reform):
            raise ValueError(
                "Pass the Reform class, not an instance: a simulation applies "
                "the class to its own tax-benefit system, so an instance's own "
                "state would be lost."
            )

        if isinstance(reform, type) and issubclass(reform, Reform):
            if _is_reform_from_dict(reform):
                dated = DatedReform(
                    reading=REFORM_FROM_DICT,
                    changes=_canonical_paths(reform.parameter_values),
                )
                return cls(
                    dated_reforms=[dated],
                    simulation_modifier=_legacy_override_modifier(dated),
                )

            reform_class = reform

            def modifier(simulation: Simulation) -> None:
                _apply_reform_class(reform_class, simulation)

            return cls(
                simulation_modifier=modifier,
            )

        elif isinstance(reform, dict):
            for parameter in reform:
                check_parameter_not_removed(parameter)
            dated = DatedReform(reading=REFORM_DICT, changes=_canonical_paths(reform))
            return cls(
                dated_reforms=[dated],
                simulation_modifier=_legacy_override_modifier(dated),
            )

        elif isinstance(reform, tuple):
            # A tuple is a sequence of reforms applied in order, matching
            # policyengine-core's Simulation.apply_reform.
            if (
                len(reform) > 1
                and isinstance(reform[0], type)
                and issubclass(reform[0], Reform)
                and not all(
                    isinstance(item, (dict, tuple))
                    or (isinstance(item, type) and issubclass(item, Reform))
                    for item in reform[1:]
                )
            ):
                raise ValueError(
                    "Unsupported reform type: the (reform_class, *args) tuple "
                    "form is no longer supported; a tuple is a sequence of "
                    "reforms applied in order."
                )
            combined = cls()
            for subreform in reform:
                combined = combined + cls.from_reform(subreform)
            return combined

        else:
            raise ValueError(
                f"Unsupported reform type: {type(reform)}. "
                "Expected a Reform class, a dict, or a tuple of these."
            )

    def apply(self, simulation: Simulation) -> None:
        """Apply this scenario to an already-built simulation.

        First applies parameter changes, then runs the simulation modifier if present.

        This edits the simulation's annualised parameters, as it always has,
        adding to whatever the simulation already carries. A dated reform's
        keys override the annualised values over their dates and are not
        annualised again, so a change dated 6 April does not set that fiscal
        year here. Pass the scenario (or ``reform=``) when constructing the
        ``Simulation`` to have its changes written onto the statutory
        timeline. The tax-benefit system keeps the edits, so a later rebuild
        of its parameters applies them again.

        Args:
            simulation: The simulation to modify
        """
        if self.dated_reforms:
            logger.warning(
                "Scenario.apply edits the built simulation's annualised "
                "parameters, so its dated reform keys are not annualised "
                "again. Pass the scenario when constructing the Simulation to "
                "apply them on the statutory timeline."
            )

        # Apply parameter changes first
        overrides: List[LegacyOverride] = []
        if self.parameter_changes:
            parameters = simulation.tax_benefit_system.parameters
            for path, value in self.parameter_changes.items():
                if isinstance(value, dict):
                    # Handle nested parameter changes
                    if not value:
                        check_parameter_not_removed(path)
                    for sub_path, sub_value in value.items():
                        full_path = f"{path}.{sub_path}"
                        check_parameter_not_removed(full_path)
                        try:
                            parameters.get_child(full_path)
                        except ValueError:
                            # A saved period-valued policy on a removed scalar
                            # path still needs the migration message; valid
                            # children such as male.age remain reformable.
                            check_parameter_not_removed(path)
                            raise
                        # Apply to all periods
                        overrides.append(
                            LegacyOverride(full_path, None, sub_value, ALL_PERIODS)
                        )
                else:
                    # Simple parameter change, applied to all periods
                    check_parameter_not_removed(path)
                    overrides.append(LegacyOverride(path, None, value, ALL_PERIODS))
        if overrides:
            _add_overrides(simulation, overrides)

        # Then apply simulation modifier
        if self.simulation_modifier:
            setattr(simulation, APPLYING_TO_BUILT_SIMULATION, True)
            try:
                self.simulation_modifier(simulation)
            finally:
                delattr(simulation, APPLYING_TO_BUILT_SIMULATION)
            # UK simulations derive paired CGT series after modifiers run.
            # Keep Scenario compatible with Core and other country simulations.
            refresh_projection = getattr(
                simulation, "_refresh_capital_gains_projection", None
            )
            if callable(refresh_projection):
                refresh_projection()

    def __repr__(self) -> str:
        """String representation of the Scenario."""
        parts = []
        if self.parameter_changes:
            parts.append(f"parameter_changes={len(self.parameter_changes)} items")
        if self.dated_reforms:
            parts.append(f"dated_reforms={len(self.dated_reforms)} items")
        if self.simulation_modifier:
            parts.append("simulation_modifier=<function>")
        return f"Scenario({', '.join(parts)})"
