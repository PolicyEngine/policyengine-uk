from policyengine_uk.model_api import *


class is_CTC_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Child Tax Credit eligibility"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 8"

    def formula(benunit, period, parameters):
        already_claiming = (
            add(benunit, period, ["child_tax_credit_reported"]) > 0
        )
        return (
            benunit.any(benunit.members("is_child_for_CTC", period))
            & already_claiming
        )
