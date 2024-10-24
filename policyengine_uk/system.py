from pathlib import Path
from policyengine_uk.entities import entities
from policyengine_core.taxbenefitsystems import TaxBenefitSystem
from policyengine_core.simulations import (
    Simulation as CoreSimulation,
    Microsimulation as CoreMicrosimulation,
)
from policyengine_uk_data import (
    DATASETS,
    EnhancedFRS_2022_23,
)
from policyengine_uk_data.storage import STORAGE_FOLDER
import pandas as pd
from policyengine_uk.utils.parameters import (
    backdate_parameters,
    convert_to_fiscal_year_parameters,
)

from policyengine_uk.reforms import create_structural_reforms_from_parameters

COUNTRY_DIR = Path(__file__).parent


class CountryTaxBenefitSystem(TaxBenefitSystem):
    parameters_dir = COUNTRY_DIR / "parameters"
    variables_dir = COUNTRY_DIR / "variables"
    auto_carry_over_input_variables = True
    basic_inputs = [
        "BRMA",
        "local_authority",
        "region",
        "employment_income",
        "age",
    ]
    modelled_policies = COUNTRY_DIR / "modelled_policies.yaml"

    def __init__(self, reform=None):
        super().__init__(entities, reform=reform)

        self.parameters = backdate_parameters(self.parameters, "2015-01-01")
        self.parameters.gov.hmrc = convert_to_fiscal_year_parameters(
            self.parameters.gov.hmrc
        )
        self.parameters.gov.dwp = convert_to_fiscal_year_parameters(
            self.parameters.gov.dwp
        )


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
    default_tax_benefit_system_instance = system
    default_dataset = EnhancedFRS_2022_23
    default_dataset_year = 2024
    default_calculation_period = 2024
    default_input_period = 2024
    default_role = "member"
    max_spiral_loops = 10
    datasets = DATASETS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        reform = create_structural_reforms_from_parameters(
            self.tax_benefit_system.parameters, "2023-01-01"
        )
        if reform is not None:
            self.apply_reform(reform)

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
