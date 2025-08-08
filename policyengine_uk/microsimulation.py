# Standard library imports
from typing import List, Optional

# Third-party imports
import numpy as np
from microdf import MicroDataFrame, MicroSeries

# PolicyEngine core imports
from policyengine_core.tracers import SimpleTracer

from .simulation import Simulation


class Microsimulation(Simulation):
    """Extended simulation class with weighting support for microsimulation.

    Provides weighted calculations using survey weights for population-level
    estimates and statistics.
    """

    def get_weights(
        self, variable_name: str, period: str, map_to: Optional[str] = None
    ) -> np.ndarray:
        """Get weights for the specified variable's entity.

        Args:
            variable_name: Name of the variable to get weights for
            period: Time period for the weights
            map_to: Optional entity key to map weights to

        Returns:
            Array of weights for the entity
        """
        variable = self.tax_benefit_system.get_variable(variable_name)
        entity_key = map_to or variable.entity.key
        weight_variable_name = f"{entity_key}_weight"
        return self.calculate(
            weight_variable_name, period, map_to=map_to, unweighted=True
        )

    def calculate(
        self,
        variable_name: str,
        period: str = None,
        map_to: str = None,
        decode_enums: bool = False,
        unweighted: bool = False,
    ):
        tracer: SimpleTracer = self.tracer
        result = super().calculate(
            variable_name, period, map_to=map_to, decode_enums=decode_enums
        )

        if not unweighted and len(tracer.stack) == 0:
            weights = self.get_weights(variable_name, period, map_to=map_to)
            return MicroSeries(result, weights=weights)

        return result

    def calculate_dataframe(
        self,
        variable_names: List[str],
        period: Optional[str] = None,
        map_to: Optional[str] = None,
        use_weights: bool = True,
    ) -> MicroDataFrame:
        """Calculate multiple variables as a weighted DataFrame.

        Args:
            variable_names: List of variable names to calculate
            period: Time period for calculation
            map_to: Optional entity key to map results to
            use_weights: Whether to apply survey weights

        Returns:
            MicroDataFrame with calculated values and weights
        """
        values = super().calculate_dataframe(variable_names, period, map_to)
        if not use_weights:
            return values
        weights = self.get_weights(variable_names[0], period, map_to=map_to)
        return MicroDataFrame(values, weights=weights)

    def compare(
        self,
        other: "Simulation",
        variables: list[str] = None,
        period: str = None,
        change_only: bool = False,
    ):
        """Compare two simulations for a specific variable list.

        Args:
            other: Another Simulation instance to compare against
            variables: List of variable names to compare. If None, compares all variables.

        Returns:
            DataFrame with comparison results
        """
        df = super().compare(
            other, variables=variables, period=period, change_only=change_only
        )
        return MicroDataFrame(
            df, weights=self.get_weights(variables[0], period)
        )
