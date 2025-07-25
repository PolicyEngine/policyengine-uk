# Standard library imports
import copy
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Type

# Third-party imports
import numpy as np
import pandas as pd
from microdf import MicroDataFrame, MicroSeries

# PolicyEngine core imports
from policyengine_core.data import Dataset
from policyengine_core.parameters.operations.propagate_parameter_metadata import (
    propagate_parameter_metadata,
)
from policyengine_core.parameters.operations.uprate_parameters import (
    uprate_parameters,
)
from policyengine_core.parameters import Parameter
from policyengine_core.reforms import Reform
from policyengine_core.simulations import Simulation as CoreSimulation
from policyengine_core.taxbenefitsystems import TaxBenefitSystem
from policyengine_core.tools.hugging_face import download_huggingface_dataset
from policyengine_core.tracers import FullTracer, SimpleTracer

# PolicyEngine UK imports
from policyengine_uk.data.dataset_schema import (
    UKMultiYearDataset,
    UKSingleYearDataset,
)
from policyengine_uk.entities import BenUnit, Household, Person
from policyengine_uk.parameters.gov.contrib.create_private_pension_uprating import (
    add_private_pension_uprating_factor,
)
from policyengine_uk.parameters.gov.dwp.state_pension.triple_lock.create_triple_lock import (
    add_triple_lock,
)
from policyengine_uk.parameters.gov.economic_assumptions.create_economic_assumption_indices import (
    create_economic_assumption_indices,
)
from policyengine_uk.parameters.gov.economic_assumptions.lag_average_earnings import (
    add_lagged_earnings,
)
from policyengine_uk.parameters.gov.economic_assumptions.lag_cpi import (
    add_lagged_cpi,
)
from policyengine_uk.utils.parameters import (
    backdate_parameters,
    convert_to_fiscal_year_parameters,
)
from policyengine_uk.utils.scenario import Scenario

# Module constants
COUNTRY_DIR = Path(__file__).parent
ENHANCED_FRS = "hf://policyengine/policyengine-uk-data/enhanced_frs_2023_24.h5"


class CountryTaxBenefitSystem(TaxBenefitSystem):
    """UK-specific tax and benefit system implementation.

    This class defines the UK tax-benefit system with all relevant
    variables, parameters, and entities (Person, BenUnit, Household).
    """

    basic_inputs: List[str] = [
        "brma",
        "local_authority",
        "region",
        "employment_income",
        "age",
    ]
    modelled_policies = COUNTRY_DIR / "modelled_policies.yaml"
    auto_carry_over_input_variables: bool = True

    def reset_parameters(self) -> None:
        """Reset parameters by reloading from the parameters directory."""
        self.load_parameters(self.parameters_dir)

    def process_parameters(self) -> None:
        """Process and transform parameters with UK-specific adjustments.

        Applies various parameter transformations including:
        - Private pension uprating factors
        - Lagged earnings and CPI indices
        - Triple lock calculations for state pensions
        - Economic assumption indices
        - Parameter uprating and backdating
        - Conversion to fiscal year parameters
        """
        # Add various UK-specific parameter adjustments
        self.parameters = add_private_pension_uprating_factor(self.parameters)
        self.parameters = add_lagged_earnings(self.parameters)
        self.parameters = add_lagged_cpi(self.parameters)
        self.parameters = add_triple_lock(self.parameters)
        self.parameters = create_economic_assumption_indices(self.parameters)

        # Create baseline parameters for reform comparisons
        self.parameters.add_child("baseline", self.parameters.clone())

        # Apply general parameter operations
        self.parameters = propagate_parameter_metadata(self.parameters)
        self.parameters = uprate_parameters(self.parameters)
        self.parameters = backdate_parameters(self.parameters, "2015-01-01")
        self.parameters.gov = convert_to_fiscal_year_parameters(
            self.parameters.gov
        )

    def __init__(self):
        """Initialize the UK tax-benefit system with entities and parameters."""
        self._parameters_at_instant_cache: Dict[str, Any] = {}
        self.variables: Dict[Any, Any] = {}

        # Create copies of entity classes to avoid modifying originals
        person, benunit, household = (
            copy.copy(Person),
            copy.copy(BenUnit),
            copy.copy(Household),
        )

        # Set up entities
        self.entities = [person, benunit, household]
        self.person_entity = person
        self.group_entities = [benunit, household]
        self.group_entity_keys = [entity.key for entity in self.group_entities]

        # Link entities to this tax-benefit system
        for entity in self.entities:
            entity.set_tax_benefit_system(self)

        self.variable_module_metadata = {}

        # Load all variables from the variables directory
        self.add_variables_from_directory(COUNTRY_DIR / "variables")

        # Set up and process parameters
        self.parameters_dir = COUNTRY_DIR / "parameters"
        self.reset_parameters()
        self.process_parameters()


# Create system instance for module-level access
system = CountryTaxBenefitSystem()
parameters = system.parameters
variables = system.variables


class Simulation(CoreSimulation):
    """UK-specific simulation class for calculating tax and benefit outcomes.

    Extends the core simulation functionality with UK-specific features
    and data handling capabilities.
    """

    default_input_period: int = 2025
    default_calculation_period: int = 2025

    def __init__(
        self,
        scenario: Optional[Scenario] = None,
        situation: Optional[Dict] = None,
        dataset: Optional[
            Union[pd.DataFrame, str, UKSingleYearDataset, UKMultiYearDataset]
        ] = None,
        trace: bool = False,
        reform: Dict | Type[Reform] = None,
    ):
        """Initialize a UK simulation.

        Args:
            scenario: A Scenario object defining a modification to the simulation
            situation: A dictionary describing the situation to simulate
            dataset: Data source - can be DataFrame, URL string, or Dataset object
            trace: Whether to enable detailed tracing of calculations
        """
        # Initialize tax-benefit rules
        self.tax_benefit_system = CountryTaxBenefitSystem()

        # Migrate Reform to Scenario

        if reform is not None:
            scenario = Scenario.from_reform(reform)

        # Apply parametric reforms here

        if scenario is not None:
            if scenario.parameter_changes is not None:
                self.apply_parameter_changes(scenario.parameter_changes)

        self.branch_name = "default"
        self.invalidated_caches = set()
        self.debug: bool = False
        self.trace: bool = trace
        self.tracer: SimpleTracer = (
            SimpleTracer() if not trace else FullTracer()
        )
        self.opt_out_cache: bool = False
        self.max_spiral_loops: int = 10
        self.memory_config = None
        self._data_storage_dir: Optional[str] = None

        self.branches: Dict[str, Simulation] = {}

        # Build simulation from appropriate source
        if situation is not None:
            self.build_from_situation(situation)
        elif isinstance(dataset, str):
            self.build_from_url(dataset)
        elif isinstance(dataset, pd.DataFrame):
            self.build_from_dataframe(dataset)
        elif isinstance(dataset, Dataset):
            self.build_from_dataset(dataset)
        elif isinstance(dataset, UKSingleYearDataset):
            self.build_from_single_year_dataset(dataset)
        elif isinstance(dataset, UKMultiYearDataset):
            self.build_from_multi_year_dataset(dataset)
        else:
            raise ValueError(f"Unsupported dataset type: {dataset.__class__}")

        # Handle behavioral responses for earnings and capital gains
        self.move_values("employment_income", "employment_income_before_lsr")
        self.move_values("capital_gains", "capital_gains_before_response")

        # Apply structural modifiers

        if scenario is not None:
            if scenario.simulation_modifier is not None:
                scenario.simulation_modifier(self)

    def apply_parameter_changes(self, changes: dict):
        self.tax_benefit_system.reset_parameters()

        for parameter in changes:
            p: Parameter = self.tax_benefit_system.parameters.get_child(
                parameter
            )
            if isinstance(changes[parameter], dict):
                # Time-period specific changes
                for time_period in changes[parameter]:
                    p.update(
                        period=time_period,
                        value=changes[parameter][time_period],
                    )
            else:
                p.update(period="eternity", value=changes[parameter])

        self.tax_benefit_system.process_parameters()

    def build_from_situation(self, situation: Dict) -> None:
        """Build simulation from a situation dictionary.

        Args:
            situation: Dictionary describing household composition and characteristics
        """
        self.build_from_populations(
            self.tax_benefit_system.instantiate_entities()
        )
        from policyengine_core.simulations.simulation_builder import (
            SimulationBuilder,
        )  # Import here to avoid circular dependency

        builder = SimulationBuilder()
        builder.default_period = self.default_input_period
        builder.build_from_dict(self.tax_benefit_system, situation, self)
        self.has_axes = builder.has_axes

    def build_from_url(self, url: str) -> None:
        """Build simulation from a HuggingFace dataset URL.

        Args:
            url: HuggingFace URL in format "hf://owner/repo/filename"

        Raises:
            ValueError: If URL is not a HuggingFace URL
        """
        if "hf://" not in url:
            raise ValueError(
                f"Non-HuggingFace URLs are currently not supported."
            )

        # Parse HuggingFace URL components
        owner, repo, filename = url.split("/")[-3:]
        if "@" in filename:
            version = filename.split("@")[-1]
            filename = filename.split("@")[0]
        else:
            version = None

        # Download dataset from HuggingFace
        dataset = download_huggingface_dataset(
            repo=f"{owner}/{repo}",
            repo_filename=filename,
            version=version,
        )

        # Determine dataset type and build accordingly
        if UKMultiYearDataset.validate_file_path(dataset, False):
            self.build_from_multi_year_dataset(UKMultiYearDataset(dataset))
        elif UKSingleYearDataset.validate_file_path(dataset, False):
            self.build_from_single_year_dataset(UKSingleYearDataset(dataset))
        else:
            self.build_from_dataset(
                Dataset.from_file(dataset, self.default_input_period)
            )

    def build_from_dataframe(self, df: pd.DataFrame) -> None:
        """Build simulation from a pandas DataFrame.

        Args:
            df: DataFrame with columns in format "variable_name__time_period"
        """

        def get_first_array(variable_name: str) -> pd.Series:
            """Extract the first array for a given variable name pattern."""
            columns = df.columns[df.columns.str.contains(variable_name + "__")]
            return df[columns[0]]

        # Extract ID columns
        (
            person_id,
            person_benunit_id,
            person_household_id,
            benunit_id,
            household_id,
        ) = map(
            get_first_array,
            [
                "person_id",
                "person_benunit_id",
                "person_household_id",
                "benunit_id",
                "household_id",
            ],
        )

        # Build entity structure
        self.build_from_ids(
            person_id,
            person_benunit_id,
            person_household_id,
            benunit_id,
            household_id,
        )

        # Set input values for each variable and time period
        for column in df:
            variable, time_period = column.split("__")
            if variable not in self.tax_benefit_system.variables:
                continue
            self.set_input(variable, time_period, df[column])

    def build_from_dataset(self, dataset: Dataset) -> None:
        """Build simulation from a Dataset object.

        Args:
            dataset: PolicyEngine Dataset object containing simulation data
        """
        data: Dict[str, Dict[str, Union[float, int, str]]] = (
            dataset.load_dataset()
        )

        def get_first_array(variable_name: str) -> np.ndarray:
            """Get the first time period's values for a variable."""
            time_period_values = data[variable_name]
            return time_period_values[list(time_period_values.keys())[0]]

        # Build entity structure from IDs
        self.build_from_ids(
            *map(
                get_first_array,
                [
                    "person_id",
                    "person_benunit_id",
                    "person_household_id",
                    "benunit_id",
                    "household_id",
                ],
            )
        )

        # Load all variable values
        for variable in data:
            for time_period in data[variable]:
                if variable not in self.tax_benefit_system.variables:
                    continue
                self.set_input(
                    variable, time_period, data[variable][time_period]
                )

    def build_from_single_year_dataset(
        self, dataset: UKSingleYearDataset
    ) -> None:
        """Build simulation from a single-year UK dataset.

        Args:
            dataset: UKSingleYearDataset containing one year of data
        """
        # Build entity structure
        self.build_from_ids(
            dataset.person.person_id,
            dataset.person.person_benunit_id,
            dataset.person.person_household_id,
            dataset.benunit.benunit_id,
            dataset.household.household_id,
        )

        # Load variable values from all tables
        for table in dataset.tables:
            for variable in table.columns:
                if variable not in self.tax_benefit_system.variables:
                    continue
                self.set_input(variable, dataset.time_period, table[variable])

    def build_from_multi_year_dataset(
        self, dataset: UKMultiYearDataset
    ) -> None:
        """Build simulation from a multi-year UK dataset.

        Args:
            dataset: UKMultiYearDataset containing multiple years of data
        """
        # Use first year to establish entity structure
        first_year = dataset[dataset.years[0]]
        self.build_from_ids(
            first_year.person.person_id,
            first_year.person.person_benunit_id,
            first_year.person.person_household_id,
            first_year.benunit.benunit_id,
            first_year.household.household_id,
        )

        # Load variable values for all years
        for year in dataset.years:
            for table in dataset[year].tables:
                for variable in table.columns:
                    if variable not in self.tax_benefit_system.variables:
                        continue
                    self.set_input(variable, year, table[variable])

    def build_from_ids(
        self,
        person_id: np.ndarray,
        person_benunit_id: np.ndarray,
        person_household_id: np.ndarray,
        benunit_id: np.ndarray,
        household_id: np.ndarray,
    ) -> None:
        """Build simulation entities from ID arrays.

        Args:
            person_id: Array of person IDs
            person_benunit_id: Array mapping persons to benefit units
            person_household_id: Array mapping persons to households
            benunit_id: Array of benefit unit IDs
            household_id: Array of household IDs
        """
        from policyengine_core.simulations.simulation_builder import (
            SimulationBuilder,
        )  # Import here to avoid circular dependency

        builder = SimulationBuilder()
        builder.populations = self.tax_benefit_system.instantiate_entities()

        # Declare entities
        builder.declare_person_entity("person", person_id)
        builder.declare_entity("benunit", np.unique(benunit_id))
        builder.declare_entity("household", np.unique(household_id))

        # Link persons to benefit units and households
        builder.join_with_persons(
            builder.populations["benunit"],
            person_benunit_id,
            np.array(["member"] * len(person_benunit_id)),
        )
        builder.join_with_persons(
            builder.populations["household"],
            person_household_id,
            np.array(["member"] * len(person_household_id)),
        )

        self.build_from_populations(builder.populations)

    def move_values(self, variable_donor: str, variable_target: str) -> None:
        """Move values from one variable to another across all branches.

        Used for behavioral response modeling where original values need
        to be preserved.

        Args:
            variable_donor: Variable to move values from
            variable_target: Variable to move values to
        """
        for simulation in list(self.branches.values()) + [self]:
            holder = simulation.get_holder(variable_donor)
            for known_period in holder.get_known_periods():
                array = holder.get_array(known_period)
                simulation.set_input(variable_target, known_period, array)
                holder.delete_arrays(known_period)


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
            weight_variable_name, period, map_to=map_to, use_weights=False
        )

    def calculate(
        self,
        variable_name: str,
        period: Optional[str] = None,
        map_to: Optional[str] = None,
        use_weights: bool = True,
        decode_enums: bool = False,
    ) -> MicroSeries:
        """Calculate variable values with optional weighting.

        Args:
            variable_name: Name of variable to calculate
            period: Time period for calculation
            map_to: Optional entity key to map results to
            use_weights: Whether to apply survey weights

        Returns:
            MicroSeries with calculated values and weights
        """
        values = super().calculate(variable_name, period, map_to, decode_enums=decode_enums)
        if not use_weights:
            return values
        weights = self.get_weights(variable_name, period, map_to)
        return MicroSeries(np.array(values), weights=weights)

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
