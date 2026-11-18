from policyengine_uk.model_api import *


class miscellaneous_income(Variable):
    value_type = float
    entity = Person
    label = "miscellaneous income"
    documentation = (
        "Income from any other source. Excludes the Warm Home Discount, "
        "which is calculated as warm_home_discount, and Guardian's Allowance "
        "cash supplied or calculated separately as guardians_allowance."
    )
    definition_period = YEAR
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
