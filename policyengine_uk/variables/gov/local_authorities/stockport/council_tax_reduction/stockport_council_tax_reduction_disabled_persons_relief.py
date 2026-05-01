from policyengine_uk.model_api import *


class stockport_council_tax_reduction_disabled_persons_relief(Variable):
    value_type = bool
    entity = Household
    label = "Stockport Council Tax Support Disabled Persons Relief"
    definition_period = YEAR
