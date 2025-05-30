from policyengine_uk.variables.household.demographic.household import (

class families(Variable):
    value_type = float
    entity = BenUnit
    label = "Variable holding families"
    definition_period = YEAR
    default_value = 1
