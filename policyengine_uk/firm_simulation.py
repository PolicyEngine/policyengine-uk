"""Firm-specific simulation class for business microdata analysis."""

from typing import Dict, Optional, Union, List
import numpy as np
import pandas as pd

from policyengine_core.simulations.simulation import Simulation
from policyengine_uk.data.firm_dataset_schema import UKFirmSingleYearDataset
from policyengine_uk.firm_tax_benefit_system import FirmTaxBenefitSystem


class FirmSimulation(Simulation):
    """Firm-specific simulation class for business microdata.

    This simulation handles firm, sector, and business_group entities
    for business-level policy analysis.
    """

    default_input_period: int = 2025
    default_calculation_period: int = 2025

    def __init__(
        self,
        dataset: Optional[Union[UKFirmSingleYearDataset, str]] = None,
        reform: Optional[Dict] = None,
        trace: bool = False,
    ):
        """Initialize a firm simulation.

        Args:
            dataset: Firm dataset or path to firm dataset
            reform: Optional reform to apply
            trace: Whether to enable tracing
        """
        # Initialize firm tax benefit system
        tax_benefit_system = FirmTaxBenefitSystem()

        if reform is not None:
            # Apply reform to the tax benefit system if needed
            pass

        # Build populations from dataset
        if isinstance(dataset, str):
            dataset = UKFirmSingleYearDataset(file_path=dataset)
        elif dataset is None:
            raise ValueError("FirmSimulation requires a firm dataset")
        elif not isinstance(dataset, UKFirmSingleYearDataset):
            raise ValueError(f"Unsupported dataset type: {dataset.__class__}")

        # Create populations using the dataset
        from policyengine_core.simulations.simulation_builder import (
            SimulationBuilder,
        )

        builder = SimulationBuilder()
        builder.populations = tax_benefit_system.instantiate_entities()

        # Declare entities
        builder.declare_person_entity("firm", dataset.firm.firm_id.values)
        builder.declare_entity("sector", dataset.sector.sector_id.values)
        builder.declare_entity(
            "business_group", dataset.business_group.business_group_id.values
        )

        # Link firms to sectors and business groups
        builder.join_with_persons(
            builder.populations["sector"],
            dataset.firm.firm_sector_id.values,
            np.array(["member"] * len(dataset.firm)),
        )
        builder.join_with_persons(
            builder.populations["business_group"],
            dataset.firm.firm_business_group_id.values,
            np.array(["member"] * len(dataset.firm)),
        )

        # Initialize the parent Simulation with populations
        super().__init__(
            tax_benefit_system=tax_benefit_system,
            populations=builder.populations,
        )

        # Set up tracing if requested
        if trace:
            self.trace = True

        # Load variable values from dataset
        for table in dataset.tables:
            for variable in table.columns:
                if variable not in self.tax_benefit_system.variables:
                    continue
                self.set_input(
                    variable, dataset.time_period, table[variable].values
                )

        self.dataset = dataset
        self.input_variables = self.get_known_variables()

    def get_known_variables(self) -> List[str]:
        """Get list of variables with known values.

        Returns:
            List of variable names that have values set
        """
        known = []
        for variable in self.tax_benefit_system.variables:
            try:
                if len(self.get_holder(variable).get_known_periods()) > 0:
                    known.append(variable)
            except:
                pass
        return known

    def calculate_dataframe(
        self,
        variable_names: List[str],
        period: Optional[int] = None,
    ) -> pd.DataFrame:
        """Calculate multiple variables and return as DataFrame.

        Args:
            variable_names: List of variables to calculate
            period: Time period for calculation

        Returns:
            DataFrame with calculated values
        """
        if period is None:
            period = self.default_calculation_period

        data = {}
        for variable in variable_names:
            data[variable] = self.calculate(variable, period)

        return pd.DataFrame(data)
