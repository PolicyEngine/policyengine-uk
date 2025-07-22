from policyengine_uk.model_api import *


class corporate_tax_incidence(Variable):
    label = "Corporate tax incidence"
    documentation = (
        "Reduction in value of corporate wealth due to taxes on corporations"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    adds = [
        "corporate_sdlt",
        "business_rates",
    ]
