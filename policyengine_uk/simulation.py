# Standard library imports
from typing import Dict, Optional, Union, Type, List

# Third-party imports
import numpy as np
import pandas as pd

# PolicyEngine core imports
from policyengine_core.data import Dataset
from policyengine_core.periods import period as period_
from policyengine_core.parameters import Parameter
from policyengine_core.reforms import Reform
from policyengine_core.simulations import Simulation as CoreSimulation
from policyengine_core.tools.hugging_face import download_huggingface_dataset
from policyengine_core.tracers import FullTracer, SimpleTracer

# PolicyEngine UK imports
from policyengine_uk.data.dataset_schema import (
    UKMultiYearDataset,
    UKSingleYearDataset,
)
from policyengine_uk.utils.scenario import Scenario
from policyengine_uk.data.economic_assumptions import (
    extend_single_year_dataset,
)
from policyengine_uk.utils.dependencies import get_variable_dependencies

from .tax_benefit_system import CountryTaxBenefitSystem

from microdf import MicroDataFrame


class Simulation(CoreSimulation):
    """UK-specific simulation class for calculating tax and benefit outcomes.

    Extends the core simulation functionality with UK-specific features
    and data handling capabilities.
    """

    default_input_period: int = 2025
    default_calculation_period: int = 2025
    baseline: "Simulation"

    calculated_periods: List[str] = []
    _variable_dependencies: Dict[str, List[str]] = None

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
        elif dataset is None:
            self.build_from_url(
                "hf://policyengine/policyengine-uk-data/enhanced_frs_2023_24.h5"
            )
        else:
            raise ValueError(f"Unsupported dataset type: {dataset.__class__}")

        self.input_variables = self.get_known_variables()

        # Universal Credit reform (July 2025). Needs closer integration in the baseline,
        # but adding here for ease of toggling on/off via the 'active' parameter.
        from policyengine_uk.scenarios import universal_credit_july_2025_reform

        universal_credit_july_2025_reform.simulation_modifier(self)

        # Apply structural modifiers

        self.tax_benefit_system.reset_parameter_caches()

        self.move_values("capital_gains", "capital_gains_before_response")
        self.move_values("employment_income", "employment_income_before_lsr")

        if scenario is not None:
            self.baseline = Simulation(
                scenario=None,
                situation=situation,
                dataset=dataset,
                trace=trace,
            )
        else:
            self.baseline = self.clone()

        if scenario is not None:
            if scenario.simulation_modifier is not None:
                scenario.simulation_modifier(self)

        self.calculated_periods = []

    def reset_calculations(self):
        for variable in self.tax_benefit_system.variables:
            if variable not in self.input_variables:
                self.delete_arrays(variable)

    def get_known_variables(self):
        variables = []
        for variable in self.tax_benefit_system.variables:
            if len(self.get_holder(variable).get_known_periods()) > 0:
                variables.append(variable)
        return variables

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
                p.update(period="year:2000:100", value=changes[parameter])

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

        self.dataset = UKSingleYearDataset.from_simulation(
            self, fiscal_year=self.default_input_period
        )

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
            dataset = Dataset.from_file(dataset, self.default_input_period)
            self.build_from_dataset(dataset)

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

        first_variable = data[list(data.keys())[0]]
        first_time_period = list(first_variable.keys())[0]

        def get_first_array(variable_name: str) -> np.ndarray:
            """Get the first time period's values for a variable."""
            time_period_values = data[variable_name]
            return time_period_values[first_time_period]

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

        # Now convert to the new UKSingleYearDataset
        self.input_variables = self.get_known_variables()
        self.dataset = dataset
        dataset = UKSingleYearDataset.from_simulation(
            self, fiscal_year=first_time_period
        )
        multi_year_dataset = extend_single_year_dataset(dataset)

        self.build_from_multi_year_dataset(multi_year_dataset)
        self.dataset = multi_year_dataset

    def build_from_single_year_dataset(
        self, dataset: UKSingleYearDataset
    ) -> None:
        """Build simulation from a single-year UK dataset.

        Args:
            dataset: UKSingleYearDataset containing one year of data
        """

        dataset = extend_single_year_dataset(dataset)
        self.build_from_multi_year_dataset(dataset)
        self.dataset = dataset

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

        self.dataset = dataset

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

    def calculate_all(self, year: int) -> None:
        person, benunit, household = (
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
        )
        period = str(year)
        for variable in self.tax_benefit_system.variables.values():
            entity = variable.entity.key
            result = self.calculate(variable.name, period).values
            if entity == "person":
                person[variable.name] = result
            elif entity == "benunit":
                benunit[variable.name] = result
            elif entity == "household":
                household[variable.name] = result

        person = MicroDataFrame(person, weights="person_weight")
        benunit = MicroDataFrame(benunit, weights="benunit_weight")
        household = MicroDataFrame(household, weights="household_weight")

        return UKSingleYearDataset(
            person=person,
            benunit=benunit,
            household=household,
            fiscal_year=year,
        )

    def calculate(
        self,
        variable_name: str = None,
        period: str = None,
        map_to: str = None,
        decode_enums: bool = False,
    ):
        if variable_name is None:
            return self.calculate_all()
        tracer: SimpleTracer = self.tracer
        if len(tracer.stack) == 0:
            # Only decode enums to string values when we're not within
            # the simulation tree.
            decode_enums = True

        if period is None:
            period = self.default_calculation_period

        period = period_(period)

        return super().calculate(
            variable_name, period, map_to=map_to, decode_enums=decode_enums
        )

    def apply_dynamics(self, year: int):
        """Apply dynamics to the simulation for a specific year.

        Args:
            year: Year to apply dynamics for
        """
        # Apply OBR labour supply dynamics if enabled
        from policyengine_uk.dynamics.labour_supply import (
            apply_labour_supply_responses,
        )

        return apply_labour_supply_responses(self, year=str(year))

    def get_variable_dependencies(self, variable_name: str, depth: int = 1):
        if self._variable_dependencies is None:
            self._variable_dependencies = {}
            self._example_simulation = Simulation(
                situation={
                    "age": 30,
                },
                trace=True,
            )
            self._example_simulation.calculate("hbai_household_net_income")
            for (
                variable
            ) in self._example_simulation.tax_benefit_system.variables:
                try:
                    dependencies = get_variable_dependencies(
                        variable, self._example_simulation
                    )
                    self._variable_dependencies[variable] = dependencies
                except Exception as e:
                    self._variable_dependencies[variable] = []

        if variable_name not in self._variable_dependencies:
            raise ValueError(
                f"Variable '{variable_name}' not found in simulation dependencies."
            )
        dependencies = self._variable_dependencies[variable_name]

        if depth <= 1:
            return dependencies

        all_dependencies = set(dependencies)
        for dep in dependencies:
            try:
                sub_dependencies = self.get_variable_dependencies(
                    dep, depth - 1
                )
                all_dependencies.update(sub_dependencies)
            except ValueError:
                continue
        return list(all_dependencies)

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

        if variables is None:
            variables = self.input_variables + [
                "hbai_household_net_income",
            ]

        df_self = self.calculate_dataframe(variables, period=period)
        df_other = other.calculate_dataframe(variables, period=period)

        df_combined = pd.concat(
            [df_self, df_other], axis=1, keys=["self", "other"]
        )
        # Reset columns, then order by variable name first then self/other
        df_combined.columns = [
            f"{var}_{entity}" for entity, var in df_combined.columns
        ]
        # Add change where applicable (numeric only)
        for variable in variables:
            self_col = f"{variable}_self"
            other_col = f"{variable}_other"
            try:
                df_combined[f"{variable}_change"] = (
                    df_combined[other_col] - df_combined[self_col]
                )
            except:
                # For other data types, use XOR
                df_combined[f"{variable}_change"] = (
                    df_combined[other_col] != df_combined[self_col]
                )
        columns = []

        for variable in variables:
            columns.extend(
                [
                    f"{variable}_self",
                    f"{variable}_other",
                    f"{variable}_change",
                ]
            )

        if change_only:
            variables_to_include = []
            for variable in variables:
                if df_combined[f"{variable}_change"].mean() > 0:
                    variables_to_include.extend(
                        [
                            f"{variable}_self",
                            f"{variable}_other",
                            f"{variable}_change",
                        ]
                    )
            columns = variables_to_include
        return df_combined[columns]
