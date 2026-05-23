from policyengine_uk.model_api import *


class disability_basic_income(Variable):
    label = "Disability basic income"
    documentation = "Flat per-week basic income paid to anyone receiving the Disability Living Allowance, Personal Independence Payment, or the Universal Credit limited capability for work-related activity element."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        amount = parameters(period).gov.contrib.disability_basic_income.amount
        receives_dla = person("dla", period) > 0
        receives_pip = person("pip", period) > 0
        receives_uc_lcwra = person("uc_limited_capability_for_WRA", period) & (
            person.benunit("universal_credit", period) > 0
        )
        eligible = receives_dla | receives_pip | receives_uc_lcwra
        return eligible * amount * WEEKS_IN_YEAR
