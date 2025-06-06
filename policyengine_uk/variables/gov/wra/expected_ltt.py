from policyengine_uk.model_api import *


class expected_ltt(Variable):
    label = "Land Transaction Tax (expected)"
    documentation = "Expected value of Land Transaction Tax"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period):
        property_sale_rate = household.state("property_sale_rate", period)
        land_transaction_tax = household("land_transaction_tax", period)
        return property_sale_rate * land_transaction_tax
