from policyengine_uk.model_api import *


class severe_disability_premium(Variable):
    value_type = float
    entity = BenUnit
    label = "Severe disability premium"
    definition_period = YEAR
    reference = "The Social Security Amendment (Enhanced Disability Premium) Regulations 2000"
    unit = GBP

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.disability_premia
        single = benunit("is_single", period.this_year)
        couple = benunit("is_couple", period.this_year)
        single_premium = single * p.severe_single
        couple_premium = couple * p.severe_couple
        has_severely_disabled_adults = (
            benunit("num_severely_disabled_adults", period.this_year) > 0
        )
        weekly_amount = single_premium + couple_premium
        return weekly_amount * WEEKS_IN_YEAR * has_severely_disabled_adults
