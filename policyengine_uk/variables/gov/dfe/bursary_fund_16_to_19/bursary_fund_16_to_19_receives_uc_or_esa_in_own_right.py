from policyengine_uk.model_api import *


class bursary_fund_16_to_19_receives_uc_or_esa_in_own_right(Variable):
    value_type = bool
    entity = Person
    label = "Receives UC or ESA in own right for 16 to 19 Bursary Fund"
    documentation = (
        "Whether the student receives Universal Credit or Employment and Support Allowance "
        "in their own right for 16 to 19 Bursary Fund purposes. This can be set explicitly "
        "in simulations; by default it uses person-level reported benefit proxies."
    )
    definition_period = YEAR
    set_input = set_input_dispatch_by_period

    def formula(person, period, parameters):
        return (person("universal_credit_reported", period) > 0) | (
            person("esa_income_reported", period)
            + person("esa_contrib_reported", period)
            > 0
        )
