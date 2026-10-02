from pydantic import BaseModel, ConfigDict
from typing import Optional, Callable, Dict, Type, Union
from policyengine_core.simulations import Simulation
from policyengine_core.reforms import Reform
from policyengine_core.periods import period, instant
from policyengine_uk.utils.parameters import (
    check_parameter_not_removed,
    uk_fiscal_year_period,
)


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

        # Return new scenario with merged configuration
        return Scenario(
            parameter_changes=merged_params if merged_params else None,
            simulation_modifier=combined_modifier,
        )

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

        A dict keeps this module's reading of its keys, including inside a
        tuple: a bare-year key such as ``"2026"`` changes that fiscal year
        only, and a scalar value applies from 2023. ``Reform.from_dict``
        (and policyengine-core's ``Simulation.apply_reform``, which turns a
        dict into one) reads a bare year as that year onwards. The two agree
        for ``"YYYY-MM-DD.YYYY-MM-DD"`` keys.

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
            reform_class = reform

            def modifier(simulation: Simulation) -> None:
                _apply_reform_class(reform_class, simulation)

            return cls(
                simulation_modifier=modifier,
            )

        elif isinstance(reform, dict):
            # Dictionary of parameter changes
            # Make sure to capture YYYY-MM-DD.YYYY-MM-DD.

            def modifier(sim: Simulation):
                for parameter in reform:
                    check_parameter_not_removed(parameter)
                    target = sim.tax_benefit_system.parameters.get_child(parameter)
                    if isinstance(reform[parameter], dict):
                        for period_str, value in reform[parameter].items():
                            if "." in period_str:
                                start = instant(period_str.split(".")[0])
                                stop = instant(period_str.split(".")[1])
                                period_ = None
                            else:
                                start = None
                                stop = None
                                period_ = (
                                    uk_fiscal_year_period(period_str)
                                    if target.metadata.get("preserve_calendar_dates")
                                    else period(period_str)
                                )
                            target.update(
                                start=start,
                                stop=stop,
                                period=period_,
                                value=value,
                            )
                    else:
                        start = instant("2023-01-01")
                        stop = None
                        period_ = None

                        target.update(
                            start=start,
                            stop=stop,
                            period=period_,
                            value=reform[parameter],
                        )

            return Scenario(
                simulation_modifier=modifier,
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
        """Apply this scenario to a simulation.

        First applies parameter changes, then runs the simulation modifier if present.

        Args:
            simulation: The simulation to modify
        """
        # Apply parameter changes first
        if self.parameter_changes:
            for path, value in self.parameter_changes.items():
                if isinstance(value, dict):
                    # Handle nested parameter changes
                    if not value:
                        check_parameter_not_removed(path)
                    for sub_path, sub_value in value.items():
                        full_path = f"{path}.{sub_path}"
                        check_parameter_not_removed(full_path)
                        try:
                            target = simulation.tax_benefit_system.parameters.get_child(
                                full_path
                            )
                        except ValueError:
                            # A saved period-valued policy on a removed scalar
                            # path still needs the migration message; valid
                            # children such as male.age remain reformable.
                            check_parameter_not_removed(path)
                            raise
                        target.update(
                            period=None,  # Apply to all periods
                            value=sub_value,
                        )
                else:
                    # Simple parameter change
                    check_parameter_not_removed(path)
                    simulation.tax_benefit_system.parameters.get_child(path).update(
                        period=None,
                        value=value,  # Apply to all periods
                    )

        # Then apply simulation modifier
        if self.simulation_modifier:
            self.simulation_modifier(simulation)

    def __repr__(self) -> str:
        """String representation of the Scenario."""
        parts = []
        if self.parameter_changes:
            parts.append(f"parameter_changes={len(self.parameter_changes)} items")
        if self.simulation_modifier:
            parts.append("simulation_modifier=<function>")
        return f"Scenario({', '.join(parts)})"
