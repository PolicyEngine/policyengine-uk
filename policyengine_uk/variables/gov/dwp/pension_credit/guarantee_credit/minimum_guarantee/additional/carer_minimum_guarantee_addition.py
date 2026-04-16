from policyengine_uk.model_api import *


class carer_minimum_guarantee_addition(Variable):
    label = "Carer-related increase"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/4"

    def formula(benunit, period, parameters):
        receives_carer_benefit = benunit.members("receives_carer_benefit", period)
        num_receiving_carers = benunit.sum(receives_carer_benefit)
        gc = parameters(period).gov.dwp.pension_credit.guarantee_credit
        return num_receiving_carers * gc.carer.addition * WEEKS_IN_YEAR
