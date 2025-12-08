# Standard library imports
import copy
from pathlib import Path
from typing import Any, Dict, List

# PolicyEngine core imports
from policyengine_core.parameters.operations.propagate_parameter_metadata import (
    propagate_parameter_metadata,
)
from policyengine_core.parameters.operations.uprate_parameters import (
    uprate_parameters,
)
from policyengine_core.taxbenefitsystems import TaxBenefitSystem
from policyengine_core.variables import Variable

# PolicyEngine UK imports
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

    variables: Dict[str, Variable]

    def reset_parameter_caches(self):
        """Reset all caches in the tax-benefit system."""
        self._parameters_at_instant_cache = {}
        for parameter in self.parameters.get_descendants():
            parameter._at_instant_cache = {}
        self.parameters._at_instant_cache = {}

    def reset_parameters(self) -> None:
        """Reset parameters by reloading from the parameters directory."""
        self._parameters_at_instant_cache = {}
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
        self._parameters_at_instant_cache = {}
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
        self.reset_parameter_caches()

    def __init__(self):
        """Initialize the UK tax-benefit system with entities and parameters."""
        self._parameters_at_instant_cache: Dict[str, Any] = {}
        self.variables = {}

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
