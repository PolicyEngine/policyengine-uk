from policyengine_uk.model_api import *


class pension_credit_standard_minimum_guarantee(Variable):
    label = "Pension Credit standard minimum guarantee"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2002/1792/regulation/6"

    def formula(benunit, period, parameters):
        relation_type = benunit("relation_type", period)
        pc = parameters(period).gov.dwp.pension_credit
        weekly_rate = pc.guarantee_credit.minimum_guarantee[relation_type]
        return weekly_rate * WEEKS_IN_YEAR
