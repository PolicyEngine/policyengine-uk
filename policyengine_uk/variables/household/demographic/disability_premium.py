from policyengine_uk.model_api import *


class disability_premium(Variable):
    value_type = float
    entity = BenUnit
    label = "Disability premium"
    documentation = (
        "Legacy benefit disability premium for the claimant or partner, using "
        "the model's existing disability indicator. The separate disabled "
        "child premium is not modelled here."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/2/paragraph/11",
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/2/paragraph/12",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/12",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/13",
    )
    unit = GBP

    def formula(benunit, period, parameters):
        dis = parameters(period).gov.dwp.disability_premia
        single = benunit("is_single", period.this_year)
        couple = benunit("is_couple", period.this_year)
        single_premium = single * dis.disability_single
        couple_premium = couple * dis.disability_couple
        has_disabled_claimant_or_partner = (
            benunit("num_disabled_claimants_or_partners_for_legacy_benefits", period)
            > 0
        )
        weekly_amount = single_premium + couple_premium
        return weekly_amount * WEEKS_IN_YEAR * has_disabled_claimant_or_partner
