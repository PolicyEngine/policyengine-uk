from policyengine_uk.model_api import *


class carer_minimum_guarantee_addition(Variable):
    label = "Carer-related increase"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/4"

    documentation = (
        "Paid for each claimant entitled to Carer's Allowance, which includes "
        "underlying entitlement where the allowance is not paid (for example "
        "under the overlapping-benefit rule), so the test is is_carer_for_benefits "
        "rather than receipt."
    )

    def formula(benunit, period, parameters):
        is_carer = benunit.members("is_carer_for_benefits", period)
        num_carers = benunit.sum(is_carer)
        gc = parameters(period).gov.dwp.pension_credit.guarantee_credit
        return num_carers * gc.carer.addition * WEEKS_IN_YEAR
