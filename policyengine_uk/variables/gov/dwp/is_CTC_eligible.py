from policyengine_uk.model_api import *


class is_CTC_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Child Tax Credit eligibility"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 8"

    def formula(benunit, period, parameters):
        already_claiming = (add(benunit, period, ["child_tax_credit_reported"]) > 0) & (
            ~add(benunit, period, ["would_claim_uc"]) > 0
        )
        return (
            benunit.any(
                benunit.members(
                    "is_child_or_qualifying_young_person_for_child_tax_credit", period
                )
            )
            & already_claiming
        )
