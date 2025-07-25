from pathlib import Path
from policyengine_uk.entities import Person, BenUnit, Household
from policyengine_core.data import Dataset
from policyengine_core.taxbenefitsystems import TaxBenefitSystem
from policyengine_core.simulations import (
    Simulation as CoreSimulation,
)
import numpy as np
from policyengine_uk.data.dataset_schema import (
    UKSingleYearDataset,
    UKMultiYearDataset,
)
from policyengine_core.tracers import SimpleTracer, FullTracer
from policyengine_uk.utils.scenario import Scenario
from policyengine_core.tools.hugging_face import download_huggingface_dataset

import pandas as pd
from policyengine_uk.utils.parameters import (
    backdate_parameters,
    convert_to_fiscal_year_parameters,
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

from policyengine_uk.parameters.gov.contrib.create_private_pension_uprating import (
    add_private_pension_uprating_factor,
)
from policyengine_uk.parameters.gov.dwp.state_pension.triple_lock.create_triple_lock import (
    add_triple_lock,
)
from policyengine_core.parameters.operations.propagate_parameter_metadata import (
    propagate_parameter_metadata,
)
from policyengine_core.parameters.operations.uprate_parameters import (
    uprate_parameters,
)
from typing import Optional, Dict, Any
import copy
from microdf import MicroSeries, MicroDataFrame

COUNTRY_DIR = Path(__file__).parent

ENHANCED_FRS = "hf://policyengine/policyengine-uk-data/enhanced_frs_2023_24.h5"


class CountryTaxBenefitSystem(TaxBenefitSystem):
    basic_inputs = [
        "brma",
        "local_authority",
        "region",
        "employment_income",
        "age",
    ]
    modelled_policies = COUNTRY_DIR / "modelled_policies.yaml"
    auto_carry_over_input_variables = True

    def reset_parameters(self):
        self.load_parameters(self.parameters_dir)

    def process_parameters(self):
        self.parameters = add_private_pension_uprating_factor(self.parameters)
        self.parameters = add_lagged_earnings(self.parameters)
        self.parameters = add_lagged_cpi(self.parameters)
        self.parameters = add_triple_lock(self.parameters)
        self.parameters = create_economic_assumption_indices(self.parameters)
        self.parameters.add_child("baseline", self.parameters.clone())
        self.parameters = propagate_parameter_metadata(self.parameters)
        self.parameters = uprate_parameters(self.parameters)
        self.parameters = backdate_parameters(self.parameters, "2015-01-01")
        self.parameters.gov = convert_to_fiscal_year_parameters(
            self.parameters.gov
        )

    def __init__(self):
        self._parameters_at_instant_cache = {}
        self.variables: Dict[Any, Any] = {}
        person, benunit, household = (
            copy.copy(Person),
            copy.copy(BenUnit),
            copy.copy(Household),
        )
        self.entities = [person, benunit, household]
        self.person_entity = person
        self.group_entities = [benunit, household]
        self.group_entity_keys = [entity.key for entity in self.group_entities]

        for entity in self.entities:
            entity.set_tax_benefit_system(self)

        self.variable_module_metadata = {}

        self.add_variables_from_directory(COUNTRY_DIR / "variables")

        self.parameters_dir = COUNTRY_DIR / "parameters"

        self.reset_parameters()

        self.process_parameters()


system = CountryTaxBenefitSystem()

parameters = system.parameters
variables = system.variables


class Simulation(CoreSimulation):
    default_input_period = 2025
    default_calculation_period = 2025

    def __init__(
        self,
        scenario: Optional[Scenario] = None,
        situation: Optional[Dict] = None,
        dataset: Optional[
            pd.DataFrame | str | UKSingleYearDataset | UKMultiYearDataset
        ] = None,
        trace: bool = False,
    ):
        # Initialise tax-benefit rules
        self.tax_benefit_system = CountryTaxBenefitSystem()
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
        self._data_storage_dir: str = None

        self.branches: Dict[str, Simulation] = {}

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

        # Earnings and gains have special treatment for behavioural responses

        self.move_values("employment_income", "employment_income_before_lsr")
        self.move_values("capital_gains", "capital_gains_before_response")

    def build_from_situation(self, situation: Dict):
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

    def build_from_url(self, url: str):
        if "hf://" not in url:
            raise ValueError(
                f"Non-HuggingFace URLs are currently not supported."
            )

        owner, repo, filename = url.split("/")[-3:]
        if "@" in filename:
            version = filename.split("@")[-1]
            filename = filename.split("@")[0]
        else:
            version = None
        dataset = download_huggingface_dataset(
            repo=f"{owner}/{repo}",
            repo_filename=filename,
            version=version,
        )

        if UKMultiYearDataset.validate_file_path(dataset, False):
            self.build_from_multi_year_dataset(UKMultiYearDataset(dataset))

        if UKSingleYearDataset.validate_file_path(dataset, False):
            self.build_from_single_year_dataset(UKSingleYearDataset(dataset))

        self.build_from_dataset(
            Dataset.from_file(dataset, self.default_input_period)
        )

    def build_from_dataframe(self, df: pd.DataFrame):
        def get_first_array(variable_name: str):
            columns = df.columns[df.columns.str.contains(variable_name + "__")]
            return df[columns[0]]

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

        self.build_from_ids(
            person_id,
            person_benunit_id,
            person_household_id,
            benunit_id,
            household_id,
        )

        for column in df:
            variable, time_period = column.split("__")
            if variable not in self.tax_benefit_system.variables:
                continue
            self.set_input(variable, time_period, df[column])

    def build_from_dataset(self, dataset: Dataset):
        data: Dict[str, Dict[str, float | int | str]] = dataset.load_dataset()

        def get_first_array(variable_name):
            time_period_values = data[variable_name]
            return time_period_values[list(time_period_values.keys())[0]]

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

        for variable in data:
            for time_period in data[variable]:
                if variable not in self.tax_benefit_system.variables:
                    continue
                self.set_input(
                    variable, time_period, data[variable][time_period]
                )

    def build_from_single_year_dataset(self, dataset: UKSingleYearDataset):
        self.build_from_ids(
            dataset.person.person_id,
            dataset.person.person_benunit_id,
            dataset.person.person_household_id,
            dataset.benunit.benunit_id,
            dataset.household.household_id,
        )

        for table in dataset.tables:
            for variable in table.columns:
                if variable not in self.tax_benefit_system.variables:
                    continue
                self.set_input(variable, dataset.time_period, table[variable])

    def build_from_multi_year_dataset(self, dataset: UKMultiYearDataset):
        first_year = dataset[dataset.years[0]]
        self.build_from_ids(
            first_year.person.person_id,
            first_year.person.person_benunit_id,
            first_year.person.person_household_id,
            first_year.benunit.benunit_id,
            first_year.household.household_id,
        )

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
        from policyengine_core.simulations.simulation_builder import (
            SimulationBuilder,
        )  # Import here to avoid circular dependency

        builder = SimulationBuilder()
        builder.populations = self.tax_benefit_system.instantiate_entities()
        builder.declare_person_entity("person", person_id)
        builder.declare_entity("benunit", np.unique(benunit_id))
        builder.declare_entity("household", np.unique(household_id))
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

    def move_values(self, variable_donor: str, variable_target: str):
        for simulation in list(self.branches.values()) + [self]:
            holder = simulation.get_holder(variable_donor)
            for known_period in holder.get_known_periods():
                array = holder.get_array(known_period)
                simulation.set_input(variable_target, known_period, array)
                holder.delete_arrays(known_period)


class Microsimulation(Simulation):

    def get_weights(
        self, variable_name: str, period: str, map_to: str = None
    ) -> np.ndarray:
        variable = self.tax_benefit_system.get_variable(variable_name)
        entity_key = map_to or variable.entity.key
        weight_variable_name = f"{entity_key}_weight"
        return self.calculate(
            weight_variable_name, period, map_to=map_to, use_weights=False
        )

    def calculate(
        self,
        variable_name: str,
        period: str = None,
        map_to: str = None,
        use_weights: bool = True,
    ) -> MicroSeries:
        values = super().calculate(variable_name, period, map_to)
        if not use_weights:
            return values
        weights = self.get_weights(variable_name, period, map_to)
        return MicroSeries(np.array(values), weights=weights)

    def calculate_dataframe(
        self,
        variable_names: list,
        period: str = None,
        map_to: str = None,
        use_weights: bool = True,
    ) -> MicroDataFrame:
        values = super().calculate_dataframe(variable_names, period, map_to)
        if not use_weights:
            return values
        weights = self.get_weights(variable_names[0], period, map_to=map_to)
        return MicroDataFrame(values, weights=weights)
