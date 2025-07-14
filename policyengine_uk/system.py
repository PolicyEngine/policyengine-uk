from pathlib import Path
from policyengine_uk.entities import entities
from policyengine_core.data import Dataset
from policyengine_core.taxbenefitsystems import TaxBenefitSystem
from policyengine_core.simulations import (
    Simulation as CoreSimulation,
    Microsimulation as CoreMicrosimulation,
)
from policyengine_uk.data.dataset_schema import UKDataset
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
from policyengine_core.reforms import Reform
from policyengine_uk.reforms import create_structural_reforms_from_parameters

from policyengine_uk.parameters.gov.contrib.create_private_pension_uprating import (
    add_private_pension_uprating_factor,
)
from policyengine_uk.parameters.gov.dwp.state_pension.triple_lock.create_triple_lock import (
    add_triple_lock,
)
from policyengine_core.parameters.operations.homogenize_parameters import (
    homogenize_parameter_structures,
)
from policyengine_core.parameters.operations.interpolate_parameters import (
    interpolate_parameters,
)
from policyengine_core.parameters.operations.propagate_parameter_metadata import (
    propagate_parameter_metadata,
)
from policyengine_core.parameters.operations.uprate_parameters import (
    uprate_parameters,
)
from policyengine_core.reforms import Reform

COUNTRY_DIR = Path(__file__).parent

ENHANCED_FRS = "hf://policyengine/policyengine-uk-data/enhanced_frs_2022_23.h5"


class CountryTaxBenefitSystem(TaxBenefitSystem):
    variables_dir = COUNTRY_DIR / "variables"
    auto_carry_over_input_variables = True
    basic_inputs = [
        "brma",
        "local_authority",
        "region",
        "employment_income",
        "age",
    ]
    modelled_policies = COUNTRY_DIR / "modelled_policies.yaml"

    def process_parameters(self, reform=None):
        if reform:
            self.apply_reform_set(reform)
        self.parameters = add_private_pension_uprating_factor(self.parameters)
        self.parameters = add_lagged_earnings(self.parameters)
        self.parameters = add_triple_lock(self.parameters)
        self.parameters = create_economic_assumption_indices(self.parameters)
        self.parameters.add_child("baseline", self.parameters.clone())
        self.parameters = homogenize_parameter_structures(
            self.parameters, self.variables
        )
        self.parameters = propagate_parameter_metadata(self.parameters)
        self.parameters = interpolate_parameters(self.parameters)
        self.parameters = uprate_parameters(self.parameters)
        self.parameters = propagate_parameter_metadata(self.parameters)
        self.add_abolition_parameters()
        self.parameters = backdate_parameters(self.parameters, "2015-01-01")

        self.parameters.gov = convert_to_fiscal_year_parameters(
            self.parameters.gov
        )

    def __init__(self, reform=None):
        super().__init__(entities, reform=reform)

        self.parameters_dir = COUNTRY_DIR / "parameters"

        self.load_parameters(self.parameters_dir)

        self.process_parameters(reform=reform)


system = CountryTaxBenefitSystem()

parameters = system.parameters
variables = system.variables


class Simulation(CoreSimulation):
    default_tax_benefit_system = CountryTaxBenefitSystem
    default_tax_benefit_system_instance = system
    default_calculation_period = 2022
    default_input_period = 2022
    default_role = "member"
    max_spiral_loops = 10

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        reform = create_structural_reforms_from_parameters(
            self.tax_benefit_system.parameters, "2023-01-01"
        )
        if reform is not None:
            self.apply_reform(reform)

        reform_dict = kwargs.get("reform")
        if reform_dict is not None:
            if isinstance(reform_dict, type):
                try:
                    reform_dict = reform_dict.parameter_values
                except:
                    reform_dict = None

        if reform_dict is not None:
            if any(["obr" in param for param in reform_dict]):
                self.tax_benefit_system.load_parameters(
                    self.tax_benefit_system.parameters_dir
                )
                Reform.from_dict(reform_dict).apply(self.tax_benefit_system)
                self.tax_benefit_system.process_parameters()

        # Labor supply responses

        employment_income = self.get_holder("employment_income")
        for known_period in employment_income.get_known_periods():
            array = employment_income.get_array(known_period)
            self.set_input("employment_income_before_lsr", known_period, array)
            employment_income.delete_arrays(known_period)

        # Capital gains responses

        cg_holder = self.get_holder("capital_gains")
        for known_period in cg_holder.get_known_periods():
            array = cg_holder.get_array(known_period)
            self.set_input(
                "capital_gains_before_response", known_period, array
            )
            employment_income.delete_arrays(known_period)


class Microsimulation(CoreMicrosimulation):
    default_tax_benefit_system = CountryTaxBenefitSystem
    default_dataset = ENHANCED_FRS
    default_dataset_year = 2022
    default_tax_benefit_system_instance = system
    default_calculation_period = 2025
    default_input_period = 2025
    default_role = "member"
    max_spiral_loops = 10

    def __init__(self, *args, dataset=ENHANCED_FRS, **kwargs):
        if dataset is not None:
            if isinstance(dataset, str):
                if "hf://" in dataset:
                    owner, repo, filename = dataset.split("/")[-3:]
                    if "@" in filename:
                        version = filename.split("@")[-1]
                        filename = filename.split("@")[0]
                    else:
                        version = None
                    dataset_file_path = download_huggingface_dataset(
                        repo=f"{owner}/{repo}",
                        repo_filename=filename,
                        version=version,
                    )

                if Path(dataset_file_path).exists():
                    if dataset_file_path.endswith(".h5"):
                        try:
                            UKDataset.validate_file_path(dataset_file_path)
                            dataset = UKDataset(file_path=dataset_file_path)
                        except:
                            dataset = Dataset.from_file(dataset_file_path)

        super().__init__(*args, dataset=dataset, **kwargs)

        reform = create_structural_reforms_from_parameters(
            self.tax_benefit_system.parameters, "2023-01-01"
        )
        if reform is not None:
            self.apply_reform(reform)

        reform_dict = kwargs.get("reform")
        if reform_dict is not None:
            if isinstance(reform_dict, type):
                try:
                    reform_dict = reform_dict.parameter_values
                except:
                    reform_dict = None

        if reform_dict is not None:
            if any(["obr" in param for param in reform_dict]):
                self.tax_benefit_system.load_parameters(
                    self.tax_benefit_system.parameters_dir
                )
                Reform.from_dict(reform_dict).apply(self.tax_benefit_system)
                self.tax_benefit_system.process_parameters()

        # Labor supply responses

        for simulation in list(self.branches.values()) + [self]:
            employment_income = simulation.get_holder("employment_income")
            for known_period in employment_income.get_known_periods():
                array = employment_income.get_array(known_period)
                simulation.set_input(
                    "employment_income_before_lsr", known_period, array
                )
                employment_income.delete_arrays(known_period)

        # Capital gains responses

        for simulation in list(self.branches.values()) + [self]:
            cg_holder = self.get_holder("capital_gains")
            for known_period in cg_holder.get_known_periods():
                array = cg_holder.get_array(known_period)
                self.set_input(
                    "capital_gains_before_response", known_period, array
                )
                employment_income.delete_arrays(known_period)
