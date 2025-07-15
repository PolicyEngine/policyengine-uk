from policyengine_uk.model_api import *


class WTC_disabled_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Working Tax Credit disabled element"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 11"
    unit = GBP
    defined_for = "is_WTC_eligible"

    def formula(benunit, period, parameters):
        WTC = parameters(period).gov.dwp.tax_credits.working_tax_credit
        person = benunit.members
        person_meets_hours = (
            person("weekly_hours", period) >= WTC.min_hours.lower
        )
        person_qualifies = (
            person_meets_hours
            & person("is_disabled_for_benefits", period)
            & person("is_adult", period)
        )
        qualifies = benunit.any(person_qualifies)
        return qualifies * WTC.elements.disabled
