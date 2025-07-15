from policyengine_uk.model_api import *


class wtc_worker_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Working Tax Credit worker element"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 11"
    unit = GBP
    defined_for = "is_wtc_eligible"

    def formula(benunit, period, parameters):
        WTC = parameters(period).gov.dwp.tax_credits.working_tax_credit
        hours = add(benunit, period, ["weekly_hours"])
        meets_hours_requirement = hours >= WTC.min_hours.default
        return meets_hours_requirement * WTC.elements.worker
