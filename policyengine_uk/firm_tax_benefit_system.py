"""Firm-specific tax benefit system for business microdata."""

import copy
from pathlib import Path
from typing import Any, Dict

from policyengine_core.taxbenefitsystems import TaxBenefitSystem
from policyengine_uk.entities import Firm, Sector, BusinessGroup
from policyengine_uk.utils.parameters import backdate_parameters

# Module constants
COUNTRY_DIR = Path(__file__).parent


class FirmTaxBenefitSystem(TaxBenefitSystem):
    """Firm-specific tax and benefit system for business microdata.

    This system handles firm, sector, and business_group entities
    for business-level analysis.
    """

    def __init__(self):
        """Initialize the firm tax-benefit system with business entities."""
        self._parameters_at_instant_cache: Dict[str, Any] = {}
        self.variables = {}

        # Create copies of entity classes to avoid modifying originals
        firm, sector, business_group = (
            copy.copy(Firm),
            copy.copy(Sector),
            copy.copy(BusinessGroup),
        )

        # Set up entities
        self.entities = [firm, sector, business_group]
        self.person_entity = (
            firm  # Firm is the "person" entity for this system
        )
        self.group_entities = [sector, business_group]
        self.group_entity_keys = [entity.key for entity in self.group_entities]

        # Link entities to this tax-benefit system
        for entity in self.entities:
            entity.set_tax_benefit_system(self)

        self.variable_module_metadata = {}

        # Add firm variables from separate directory
        variables_firm_directory = COUNTRY_DIR / "variables_firm"
        self.add_variables_from_directory(variables_firm_directory)

        # Add parameters (if needed for firm calculations)
        parameters_directory = COUNTRY_DIR / "parameters"
        if parameters_directory.exists():
            self.load_parameters(str(parameters_directory))
            backdate_parameters(self.parameters)

    def reset_parameter_caches(self):
        """Reset parameter caches (compatibility method)."""
        self._parameters_at_instant_cache = {}
