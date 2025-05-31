from policyengine_uk.model_api import *


class hbai_excluded_income(Variable):
    label = "HBAI-excluded income"
    documentation = (
        "Total value of income not included in HBAI household net income"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        VARIABLES = [
            "corporate_tax_incidence",
        ]
        return -add(household, period, VARIABLES)
