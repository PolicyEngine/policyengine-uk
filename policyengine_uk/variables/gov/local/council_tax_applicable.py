from policyengine_uk.model_api import *


class council_tax_applicable(Variable):
    value_type = float
    entity = Household
    label = "Council Tax (after abolition check)"
    documentation = "Council Tax amount, or zero if council tax is abolished"
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW

    def formula(household, period, parameters):
        council_tax = household("council_tax", period)
        abolish = parameters(period).gov.contrib.abolish_council_tax
        return where(abolish, 0, council_tax)
