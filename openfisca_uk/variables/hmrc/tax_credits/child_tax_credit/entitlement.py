from openfisca_uk.model_api import *

class maximum_ctc(Variable):
    label = "CTC maximum rate"
    documentation = "The Child Tax Credit entitlement, before means-testing"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        allowed = parameters(period).hmrc.tax_credits.child_tax_credit.elements.allowed
        return sum([benunit(element, period) for element in allowed])
