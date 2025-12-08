from policyengine_uk.model_api import *


class num_vehicles(Variable):
    label = "number of vehicles owned by the household"
    documentation = "Imputed from WAS vcarnr7 variable"
    entity = Household
    definition_period = YEAR
    value_type = int
