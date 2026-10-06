from policyengine_uk.model_api import *


class carer_premium(Variable):
    value_type = float
    entity = BenUnit
    label = "Carer premium"
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/17",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3/paragraph/9",
    )
    documentation = (
        "Carer premium for claimants and partners entitled to Carer's "
        "Allowance or Carer Support Payment, including entitlement reduced "
        "to nil by overlapping benefits. Caring hours alone do not qualify."
    )
    unit = GBP

    def formula(benunit, period, parameters):
        entitled = benunit.members("is_entitled_to_carer_benefit", period)
        claimant_or_partner = benunit.members("is_claimant_or_partner", period)
        carers = benunit.sum(entitled & claimant_or_partner)
        CP = parameters(period).gov.dwp.carer_premium
        weekly_premium = select(
            [carers >= 2, carers == 1],
            [CP.couple, CP.single],
        )
        return weekly_premium * WEEKS_IN_YEAR
