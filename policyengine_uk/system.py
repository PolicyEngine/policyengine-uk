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
    FRS_2020_21,
    CalibratedSPIEnhancedPooledFRS_2018_20,
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

    def __init__(self):
        super().__init__(entities)

        self.parameters.add_child("baseline", self.parameters.clone())


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


class Microsimulation(CoreMicrosimulation):
    default_tax_benefit_system = CountryTaxBenefitSystem
    default_tax_benefit_system_instance = system
    default_dataset = EnhancedFRS
    default_dataset_year = 2023
    default_calculation_period = 2023
    default_input_period = 2023
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


class IndividualSim(CoreIndividualSim):  # Deprecated
    tax_benefit_system = CountryTaxBenefitSystem
    entities = {entity.key: entity for entity in entities}
    default_dataset = EnhancedFRS
    required_entities = None


BASELINE_VARIABLES = {
    variable.name: variable for variable in system.variables.values()
}
