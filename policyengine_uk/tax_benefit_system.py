# Standard library imports
import copy
from pathlib import Path
from typing import Any, Dict, List

# PolicyEngine core imports
from policyengine_core import periods
from policyengine_core.parameters.operations.propagate_parameter_metadata import (
    propagate_parameter_metadata,
)
from policyengine_core.parameters.operations.uprate_parameters import (
    uprate_parameters,
)
from policyengine_core.parameters.parameter_node_at_instant import (
    ParameterNodeAtInstant,
)
from policyengine_core.periods import Instant, Period
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
    convert_instant_to_fiscal_year,
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

    def get_parameters_at_instant(
        self, instant: Instant
    ) -> ParameterNodeAtInstant:
        """
        Get parameters at an instant, with UK fiscal year adjustment.

        The UK fiscal year runs April 6 to April 5. When querying for a year
        (e.g., "2026" or January 1, 2026), this method converts the instant
        to April 30 of that year to get the correct fiscal year value.

        This ensures that queries like param("2026") return the value for
        fiscal year 2026/27 (April 6, 2026 - April 5, 2027) rather than
        the January 1, 2026 value.

        Args:
            instant: The instant to query, as string, int, Period, or Instant

        Returns:
            ParameterNodeAtInstant with all parameter values at that instant
        """
        # Convert to Instant if needed
        if isinstance(instant, Period):
            instant = instant.start
        elif isinstance(instant, (str, int)):
            instant = periods.instant(instant)
        else:
            assert isinstance(
                instant, Instant
            ), f"Expected Instant, got: {instant}"

        # Apply UK fiscal year conversion
        # If querying January 1 of a year, convert to April 30 to get
        # the fiscal year value (UK tax year starts April 6)
        instant_str = str(instant)
        fiscal_instant_str = convert_instant_to_fiscal_year(instant_str)
        fiscal_instant = periods.instant(fiscal_instant_str)

        # Use fiscal instant for cache key and lookup
        parameters_at_instant = self._parameters_at_instant_cache.get(
            fiscal_instant
        )
        if parameters_at_instant is None and self.parameters is not None:
            parameters_at_instant = self.parameters.get_at_instant(
                str(fiscal_instant)
            )
            self._parameters_at_instant_cache[fiscal_instant] = (
                parameters_at_instant
            )
        return parameters_at_instant

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
