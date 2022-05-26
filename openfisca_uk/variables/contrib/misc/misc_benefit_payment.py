from openfisca_uk.model_api import *


class misc_benefit_payment(Variable):
    label = "Payment to households on means-tested benefits"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        benefit_payment = parameters(period).contrib.misc.benefit_payment
        qualifies = (
            add(household, period, benefit_payment.qualifying_benefits) > 0
        )
        return qualifies * benefit_payment.payment
