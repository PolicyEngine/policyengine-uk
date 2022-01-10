from openfisca_uk.model_api import *

class maximum_wtc(Variable):
    label = "WTC maximum rate"
    documentation = "Working Tax Credit entitlement, before means-testing"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        allowed = parameters(period).hmrc.tax_credits.working_tax_credit.elements.allowed
        return sum([benunit(element, period) for element in allowed])
