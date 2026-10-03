from policyengine_uk.model_api import *


class severe_disability_premium(Variable):
    value_type = float
    entity = BenUnit
    label = "Severe disability premium"
    documentation = (
        "Legacy benefit severe disability premium using the model's existing "
        "severe-disability indicator for the claimant or partner. The current "
        "approximation pays the couple rate when either partner qualifies; "
        "the statutory requirement for both partners to qualify and the "
        "non-dependant and carer exclusions remain unmodelled."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/2/paragraph/13",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/14",
    )
    unit = GBP

    def formula(benunit, period, parameters):
        dis = parameters(period).gov.dwp.disability_premia
        single = benunit("is_single", period.this_year)
        couple = benunit("is_couple", period.this_year)
        single_premium = single * dis.severe_single
        couple_premium = couple * dis.severe_couple
        has_severely_disabled_claimant_or_partner = (
            benunit(
                "num_severely_disabled_claimants_or_partners_for_legacy_benefits",
                period,
            )
            > 0
        )
        weekly_amount = single_premium + couple_premium
        return weekly_amount * WEEKS_IN_YEAR * has_severely_disabled_claimant_or_partner
