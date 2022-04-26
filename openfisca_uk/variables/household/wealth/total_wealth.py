from openfisca_uk.model_api import *


@uprated(by="wealth.national_balance_sheet.household.net_worth")
class total_wealth(Variable):
    label = "Total wealth"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    formula = sum_of_variables(["property_wealth", "corporate_wealth"])
