from pathlib import Path
from policyengine_uk.entities import entities
from policyengine_core.taxbenefitsystems import TaxBenefitSystem
from policyengine_core.simulations import (
    Simulation as CoreSimulation,
    Microsimulation as CoreMicrosimulation,
)
from policyengine_uk.data.storage import STORAGE_FOLDER
from policyengine_uk.data import *
import pandas as pd

COUNTRY_FOLDER = Path(__file__).parent


class CountryTaxBenefitSystem(TaxBenefitSystem):
    parameters_dir = COUNTRY_FOLDER / "parameters"
    variables_dir = COUNTRY_FOLDER / "variables"
    auto_carry_over_input_variables = True
    modelled_policies = COUNTRY_FOLDER / "modelled_policies.yaml"

    def __init__(self):
        super().__init__(entities)


system = CountryTaxBenefitSystem()

parameters = system.parameters
variables = system.variables


class Simulation(CoreSimulation):
    default_tax_benefit_system = CountryTaxBenefitSystem
    default_tax_benefit_system_instance = system
    default_calculation_period = 2024
    default_input_period = 2024
    default_role = "member"
    max_spiral_loops = 10

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Microsimulation(CoreMicrosimulation):
    default_tax_benefit_system = CountryTaxBenefitSystem
    default_tax_benefit_system_instance = system
    default_dataset = FRS
    default_calculation_period = 2024
    default_input_period = 2024
    default_role = "member"
    max_spiral_loops = 10
    datasets = DATASETS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
