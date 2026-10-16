import copy
import logging

from pydantic import BaseModel, ConfigDict, PrivateAttr
from typing import Any, Literal, List, Optional, Callable, Dict, Tuple, Type, Union
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
    read_override_reform,
    reform_modifiers_are_effective,
    unwritten_reform_overrides,
    validate_annualised_overrides,
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
    """Changes keyed by canonical parameter paths (labour supply aliases)."""
    from policyengine_uk.parameters.gov.simulation.labour_supply_responses.aliases import (
        canonicalize_parameter_changes,
    )

    return canonicalize_parameter_changes(changes)


def _is_reform_from_dict(reform: Type[Reform]) -> bool:
    """Whether a Reform class was built by ``Reform.from_dict``."""
    return reform.__qualname__ == "Reform.from_dict.<locals>.reform" and isinstance(
        getattr(reform, "parameter_values", None), dict
    )


def _legacy_override_modifier(dated: DatedReform) -> Callable[[Simulation], None]:
    """Override changes that are no longer effective on the simulation.

    Construction retains its statutory and legacy readings. On copies,
    already-effective reforms (including legacy single-day keys) are no-ops;
    external overrides still require a key containing a 1 January value.
    """

    def modifier(simulation: Simulation) -> None:
        _reset_uc_health_warning(simulation, (dated,))
        from policyengine_uk.tax_benefit_system import (
            parameter_reads_calendar_years,
            reform_parameter_defines,
        )

        # Scenario.apply edits an already-built simulation's annualised
        # parameters, so there every change of the reform is an override.
        every_change = getattr(simulation, APPLYING_TO_BUILT_SIMULATION, False)
        if every_change:
            _, legacy = read_override_reform(
                dated.changes, dated.reading, lambda path: False
            )
            overriding = True
        elif dated in (getattr(simulation, "_building_dated_reforms", None) or ()):
            _, legacy = dated.read(
                reform_parameter_defines(),
                warn=True,
                calendar_years=parameter_reads_calendar_years(),
            )
            overriding = False
        elif reform_modifiers_are_effective((dated,), simulation.tax_benefit_system):
            legacy, overriding = [], False
        else:
            legacy, overriding = unwritten_reform_overrides(
                dated.changes,
                dated.reading,
                reform_parameter_defines(),
                getattr(simulation.tax_benefit_system, "dated_assignments", ()),
                parameter_reads_calendar_years(),
                simulation.tax_benefit_system,
            )
            overriding = overriding or (
                bool(legacy)
                and dated
                not in (getattr(simulation, "_building_dated_reforms", None) or ())
            )
        if legacy:
            if overriding:
                if not every_change:
                    _warn_annualised_overrides()
            validate_annualised_overrides(
                simulation.tax_benefit_system.parameters,
                legacy,
                require_annual_value=overriding,
                defer_invalid_keys=True,
            )
            try:
                _add_overrides(simulation, legacy)
            except (ValueError, TypeError, KeyError):
                validate_annualised_overrides(
                    simulation.tax_benefit_system.parameters,
                    legacy,
                    require_annual_value=overriding,
                )
                raise
        from policyengine_uk.scenarios.uc_reform import warn_shadowed_lcwra_reform

        warn_shadowed_lcwra_reform(simulation)

    modifier._dated_reforms = (dated,)
    return modifier


def _reset_uc_health_warning(simulation, dated_reforms, parameter_changes=None):
    """An amount reform gets one diagnostic for this application."""
    from policyengine_uk.scenarios.uc_reform import LCWRA_AMOUNT

    if LCWRA_AMOUNT in (parameter_changes or {}) or any(
        LCWRA_AMOUNT in dated.changes for dated in dated_reforms
    ):
        simulation._uc_health_amount_warning_emitted = False


def _warn_annualised_overrides() -> None:
    logger.warning(
        "Scenario.apply edits the built simulation's annualised "
        "parameters, so its dated reform keys are not annualised "
        "again. Pass the scenario when constructing the Simulation to "
        "apply them on the statutory timeline."
    )


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


def _chain(
    first: Optional[Callable[[Simulation], None]],
    second: Optional[Callable[[Simulation], None]],
) -> Optional[Callable[[Simulation], None]]:
    """A modifier that runs ``first`` and then ``second``, either of them None."""
    if first and second:
        first_dated = getattr(first, "_dated_reforms", None)
        second_dated = getattr(second, "_dated_reforms", None)
        dated = (
            first_dated + second_dated
            if first_dated is not None and second_dated is not None
            else None
        )

        def chained(simulation: Simulation) -> None:
            deferred = getattr(simulation, "_defer_uc_health_warning", False)
            _reset_uc_health_warning(simulation, dated or ())
            simulation._defer_uc_health_warning = True
            try:
                already_effective = (
                    dated is not None
                    and not getattr(simulation, APPLYING_TO_BUILT_SIMULATION, False)
                    and not getattr(simulation, "_building_dated_reforms", None)
                    and reform_modifiers_are_effective(
                        dated, simulation.tax_benefit_system
                    )
                )
                if not already_effective:
                    first(simulation)
                    second(simulation)
            finally:
                simulation._defer_uc_health_warning = deferred
            if not deferred:
                from policyengine_uk.scenarios.uc_reform import (
                    warn_shadowed_lcwra_reform,
                )

                warn_shadowed_lcwra_reform(simulation)

        chained._dated_reforms = dated
        return chained
    return first or second


class Scenario(BaseModel):
    """Represents a scenario configuration for policy simulations.

    A scenario can include parameter changes and/or simulation modifications
    that are applied before running a simulation. Scenarios can be combined
    using the + operator, and a sum runs each part's modifier at the part's
    own time (see ``parts_by_data_load``).
    """

    applied_before_data_load: bool = False
    """Whether ``Simulation`` applies the scenario before it builds its data, so the data's projected years follow its changes. A sum is applied before data load when every part that changes something is; a sum of parts applied at different times reads False here, runs each part's modifier at the part's own time and applies all its parameter changes before data load."""

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

    # A sum of parts applied at different times keeps the modifiers of the
    # parts applied before data load and of the rest, each chained in the
    # order added, for ``parts_by_data_load``; and its own flag and modifier
    # as they were when it was made, so a sum whose flag or modifier is
    # changed afterwards is applied as one scenario, as its fields say.
    _timed_modifiers: Optional[tuple] = PrivateAttr(default=None)
    _made_with: Optional[tuple] = PrivateAttr(default=None)

    def __add__(self, other: "Scenario") -> "Scenario":
        """Combine two scenarios by merging parameter changes and chaining modifiers.

        The fields of the sum hold both scenarios, as they always have:
        ``Scenario.apply`` and code that reads the fields see the whole sum.
        ``Simulation`` runs each part's modifier at the part's own time,
        before or after it builds its data (see ``parts_by_data_load``), so
        adding a scenario applied before data load, such as
        ``no_economic_assumptions``, to another keeps it before data load. A
        scenario that changes nothing has no timing of its own:
        ``Scenario() + scenario`` is applied when ``scenario`` is.

        Args:
            other: Another Scenario to combine with this one

        Returns:
            A new Scenario with merged parameter changes and combined modifiers
        """
        # Merge parameter changes (other's changes take precedence in conflicts),
        # keyed by canonical paths, so a parameter spelled two ways merges as
        # one.
        merged_params = {}

        if self.parameter_changes:
            merged_params.update(_canonical_paths(self.parameter_changes))

        if other.parameter_changes:
            for key, value in _canonical_paths(other.parameter_changes).items():
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

        # Chain simulation modifiers, as they are when the scenarios are
        # added, as the modifiers kept by timing below are.
        combined_modifier = _chain(self.simulation_modifier, other.simulation_modifier)

        dated_reforms = (self.dated_reforms or []) + (other.dated_reforms or [])

        timings = self._timings() | other._timings()

        # Return new scenario with merged configuration
        combined = Scenario(
            applied_before_data_load=timings == {True},
            parameter_changes=merged_params if merged_params else None,
            dated_reforms=dated_reforms or None,
            simulation_modifier=combined_modifier,
        )
        if len(timings) > 1:
            (first_before, first_after), (second_before, second_after) = (
                self._modifiers_by_timing(),
                other._modifiers_by_timing(),
            )
            combined._timed_modifiers = (
                _chain(first_before, second_before),
                _chain(first_after, second_after),
            )
            combined._made_with = (False, combined_modifier)
        return combined

    def __deepcopy__(self, memo: Optional[dict] = None) -> "Scenario":
        # One memo for the fields and the private attributes, so a copy of a
        # sum keeps the modifiers it keeps by timing those its fields chain.
        # A callable object among them is copied; a function, such as the
        # chained modifier, is not, so it still calls the original.
        return super().__deepcopy__({} if memo is None else memo)

    def _changes_something(self) -> bool:
        return bool(
            self.parameter_changes or self.dated_reforms or self.simulation_modifier
        )

    def _current_timed_modifiers(self) -> Optional[tuple]:
        """A sum's modifiers by timing, unless its flag or modifier has
        changed since it was made."""
        if self._timed_modifiers is None:
            return None
        flag, modifier = self._made_with
        if (
            self.applied_before_data_load == flag
            and self.simulation_modifier is modifier
        ):
            return self._timed_modifiers
        return None

    def _timings(self) -> set:
        """When the scenario's parts are applied: before data load (True),
        after it (False), both, or neither for a scenario that changes
        nothing."""
        if self._current_timed_modifiers() is not None:
            return {True, False}
        if not self._changes_something():
            return set()
        return {self.applied_before_data_load}

    def _modifiers_by_timing(self) -> tuple:
        """The modifiers run before data load and after it."""
        timed = self._current_timed_modifiers()
        if timed is not None:
            return timed
        if self.applied_before_data_load:
            return self.simulation_modifier, None
        return None, self.simulation_modifier

    def parts_by_data_load(
        self,
    ) -> Tuple[Optional["Scenario"], Optional["Scenario"]]:
        """What ``Simulation`` applies before it builds its data, and after.

        ``Simulation`` applies the first part's parameter changes and then
        its modifier before it builds its data; and the second part's
        parameter changes just after the data is built and its modifier at
        the end. A scenario is one or the other, as
        ``applied_before_data_load`` says.

        A sum of parts applied at different times runs each part's modifier
        at the part's own time: those of the parts applied before data load
        before it, in the order added, and the rest at the end. Its parameter
        changes all come first, before the data is built, as ``+`` merged
        them (the precedence ``Scenario.apply`` gives them): changing the
        parameters rebuilds them, which would discard the edits of a
        modifier that has already run. So the first part has every parameter
        change of the sum, and the second, if any part applied after data
        load has a modifier, has only that modifier. The data's projected
        years therefore follow the parameter changes of every part of such
        a sum.

        A sum whose ``applied_before_data_load`` or ``simulation_modifier``
        has been changed since it was made is applied as one scenario, as
        its fields say.

        Returns:
            The part applied before data load and the part applied after it,
            each a Scenario, or None where there is no such part.
        """
        timed = self._current_timed_modifiers()
        if timed is None:
            return (self, None) if self.applied_before_data_load else (None, self)
        before_modifier, after_modifier = timed
        before = Scenario(
            applied_before_data_load=True,
            parameter_changes=copy.deepcopy(self.parameter_changes),
            dated_reforms=copy.deepcopy(self.dated_reforms),
            simulation_modifier=before_modifier,
        )
        after = (
            Scenario(simulation_modifier=after_modifier)
            if after_modifier is not None
            else None
        )
        return before, after

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
        _reset_uc_health_warning(
            simulation, self.dated_reforms or (), self.parameter_changes
        )
        if self.dated_reforms:
            _warn_annualised_overrides()

        # Apply parameter changes first
        overrides: List[LegacyOverride] = []
        if self.parameter_changes:
            parameters = simulation.tax_benefit_system.parameters
            # Keyed by canonical paths, as a sum of scenarios already is, so a
            # deprecated alias path changes the parameter formulas read.
            for path, value in _canonical_paths(self.parameter_changes).items():
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
            deferred = getattr(simulation, "_defer_uc_health_warning", False)
            simulation._defer_uc_health_warning = True
            setattr(simulation, APPLYING_TO_BUILT_SIMULATION, True)
            try:
                self.simulation_modifier(simulation)
            finally:
                delattr(simulation, APPLYING_TO_BUILT_SIMULATION)
                simulation._defer_uc_health_warning = deferred
            # UK simulations derive paired CGT series after modifiers run.
            # Keep Scenario compatible with Core and other country simulations.
            refresh_projection = getattr(
                simulation, "_refresh_capital_gains_projection", None
            )
            if callable(refresh_projection):
                refresh_projection()
        from policyengine_uk.scenarios.uc_reform import warn_shadowed_lcwra_reform

        warn_shadowed_lcwra_reform(simulation)

    def __repr__(self) -> str:
        """String representation of the Scenario."""
        parts = []
        if self.parameter_changes:
            parts.append(f"parameter_changes={len(self.parameter_changes)} items")
        if self.dated_reforms:
            parts.append(f"dated_reforms={len(self.dated_reforms)} items")
        if self.simulation_modifier:
            parts.append("simulation_modifier=<function>")
        if self._current_timed_modifiers() is not None:
            parts.append("modifiers applied before and after data load")
        elif self.applied_before_data_load:
            parts.append("applied_before_data_load=True")
        return f"Scenario({', '.join(parts)})"
