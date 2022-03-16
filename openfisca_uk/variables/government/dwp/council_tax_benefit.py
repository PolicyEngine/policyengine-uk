from openfisca_uk.model_api import *


class council_tax_benefit_reported(Variable):
    value_type = float
    entity = Person
    label = "Council Tax Benefit (reported)"
    documentation = "Reported amount of Council Tax Benefit"
    definition_period = YEAR
    unit = "currency-GBP"


class council_tax_benefit(Variable):
    value_type = float
    entity = BenUnit
    label = "Council Tax Benefit"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["council_tax_benefit_reported"])
