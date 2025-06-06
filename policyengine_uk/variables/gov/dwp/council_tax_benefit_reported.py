from policyengine_uk.model_api import *


class council_tax_benefit_reported(Variable):
    value_type = float
    entity = Person
    label = "Council Tax Benefit (reported)"
    documentation = "Reported amount of Council Tax Benefit"
    definition_period = YEAR
    unit = GBP
