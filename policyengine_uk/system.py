from pathlib import Path
from policyengine_uk.entities import entities
from policyengine_core.taxbenefitsystems import TaxBenefitSystem
from policyengine_core.simulations import (
    Simulation as CoreSimulation,
    Microsimulation as CoreMicrosimulation,
    IndividualSim as CoreIndividualSim,
)
from policyengine_uk.data import (
    DATASETS,
    EnhancedFRS,
)
from policyengine_uk.data.storage import STORAGE_FOLDER
import pandas as pd
from policyengine_uk.tools.parameters import backdate_parameters

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

        self.parameters = backdate_parameters(self.parameters, "2021-01-01")


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


class Microsimulation(CoreMicrosimulation):
    default_tax_benefit_system = CountryTaxBenefitSystem
    default_tax_benefit_system_instance = system
    default_dataset = EnhancedFRS
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


class IndividualSim(CoreIndividualSim):  # Deprecated
    tax_benefit_system = CountryTaxBenefitSystem
    entities = {entity.key: entity for entity in entities}
    default_dataset = EnhancedFRS
    required_entities = None


BASELINE_VARIABLES = {
    variable.name: variable for variable in system.variables.values()
}
