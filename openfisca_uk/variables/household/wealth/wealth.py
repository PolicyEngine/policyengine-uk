from openfisca_uk.model_api import *


class total_wealth(Variable):
    label = "Total wealth"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    formula = sum_of_variables(["property_wealth", "corporate_wealth"])
