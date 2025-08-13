from pydantic import BaseModel
from typing import Optional, Callable, Dict, Type, Union
from policyengine_core.simulations import Simulation
from policyengine_core.reforms import Reform
from policyengine_core.periods import period, instant


class Scenario(BaseModel):
    """Represents a scenario configuration for policy simulations.

    A scenario can include parameter changes and/or simulation modifications
    that are applied before running a simulation. Scenarios can be combined
    using the + operator.
    """

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

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True  # Allow Callable types

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
    def from_reform(
        cls, reform: Union[tuple, dict, Type[Reform]]
    ) -> "Scenario":
        """Create a Scenario from various reform representations.

        Args:
            reform: Can be:
                - A Reform class type (will be applied via simulation modifier)
                - A dict of parameter changes
                - A tuple (treated as a Reform for backward compatibility)

        Returns:
            A new Scenario configured with the reform

        Raises:
            ValueError: If reform type is not supported
        """
        if isinstance(reform, type) and issubclass(reform, Reform):
            # Reform class - create modifier function
            def modifier(simulation: Simulation) -> None:
                reform_instance = reform()
                reform_instance.apply(simulation.tax_benefit_system)

            return cls(
                simulation_modifier=modifier,
            )

        elif isinstance(reform, dict):
            # Dictionary of parameter changes
            # Make sure to capture YYYY-MM-DD.YYYY-MM-DD.

            def modifier(sim: Simulation):
                for parameter in reform:
                    if isinstance(reform[parameter], dict):
                        for period_str, value in reform[parameter].items():
                            if "." in period_str:
                                start = instant(period_str.split(".")[0])
                                stop = instant(period_str.split(".")[1])
                                period_ = None
                            else:
                                period_ = period(period_str)
                            sim.tax_benefit_system.parameters.get_child(
                                parameter
                            ).update(
                                start=start,
                                stop=stop,
                                period=period_,
                                value=value,
                            )
                    else:
                        start = instant("2023-01-01")
                        stop = None
                        period_ = None

                        sim.tax_benefit_system.parameters.get_child(
                            parameter
                        ).update(
                            start=start,
                            stop=stop,
                            period=period_,
                            value=reform[parameter],
                        )

            return Scenario(
                simulation_modifier=modifier,
            )

        elif isinstance(reform, tuple):
            # Tuple format (legacy support) - treat as a Reform class
            # Assuming the tuple contains (reform_class, *args)
            if (
                len(reform) > 0
                and isinstance(reform[0], type)
                and issubclass(reform[0], Reform)
            ):
                reform_class = reform[0]
                reform_args = reform[1:] if len(reform) > 1 else ()

                def modifier(simulation: Simulation) -> None:
                    reform_instance = reform_class(*reform_args)
                    reform_instance.apply(simulation.tax_benefit_system)

                return cls(
                    simulation_modifier=modifier,
                )
            else:
                raise ValueError(f"Invalid tuple format for reform: {reform}")

        else:
            raise ValueError(
                f"Unsupported reform type: {type(reform)}. "
                "Expected Reform class, dict, or tuple."
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
                    for sub_path, sub_value in value.items():
                        full_path = f"{path}.{sub_path}"
                        simulation.tax_benefit_system.parameters.update(
                            full_path,
                            period=None,  # Apply to all periods
                            value=sub_value,
                        )
                else:
                    # Simple parameter change
                    simulation.tax_benefit_system.parameters.update(
                        path,
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
            parts.append(
                f"parameter_changes={len(self.parameter_changes)} items"
            )
        if self.simulation_modifier:
            parts.append("simulation_modifier=<function>")
        return f"Scenario({', '.join(parts)})"
