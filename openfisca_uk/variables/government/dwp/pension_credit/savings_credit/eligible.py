from openfisca_uk.model_api import *


class savings_credit_eligible(Variable):
    label = "Eligible for Savings Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = bool
    unit = "currency-GBP"
    reference = "https://www.legislation.gov.uk/ukpga/2002/16/section/3"

    def formula(benunit, period, parameters):
        income = benunit("savings_credit_income", period)
        sc = parameters(period).dwp.pension_credit.savings_credit
        relation_type = benunit("relation_type", period)
        threshold = sc.threshold[relation_type]
        return income >= threshold
