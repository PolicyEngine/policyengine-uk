from policyengine_uk.model_api import *


class carer_minimum_guarantee_addition(Variable):
    label = "Carer-related increase"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/4"

    documentation = (
        "Paid for each claimant or partner entitled to Carer's Allowance or "
        "Carer Support Payment, including an entitlement reduced to nil by "
        "overlapping benefits. Caring hours alone, without entitlement, do "
        "not qualify."
    )

    def formula(benunit, period, parameters):
        is_carer = benunit.members("is_entitled_to_carer_benefit", period)
        is_claimant_or_partner = benunit.members("is_claimant_or_partner", period)
        num_carers = benunit.sum(is_carer & is_claimant_or_partner)
        gc = parameters(period).gov.dwp.pension_credit.guarantee_credit
        return num_carers * gc.carer.addition * WEEKS_IN_YEAR
