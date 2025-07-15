from policyengine_uk.model_api import *


class is_benefit_cap_exempt(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether exempt from the benefits cap"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        QUAL_PERSONAL_BENEFITS = [
            "carers_allowance",
            "dla",
            "esa_contrib",
        ]
        QUAL_BENUNIT_BENEFITS = ["working_tax_credit", "esa_income"]
        qualifying_benunit_benefits = add(
            benunit, period, QUAL_BENUNIT_BENEFITS
        )
        qualifying_personal_benefits = add(
            benunit, period, QUAL_PERSONAL_BENEFITS
        )
        return (qualifying_personal_benefits + qualifying_benunit_benefits) > 0
