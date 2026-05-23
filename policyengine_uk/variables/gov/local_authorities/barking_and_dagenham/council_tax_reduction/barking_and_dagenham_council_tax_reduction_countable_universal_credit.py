from policyengine_uk.model_api import *


class barking_and_dagenham_council_tax_reduction_countable_universal_credit(Variable):
    value_type = float
    entity = BenUnit
    label = "Barking and Dagenham CTS countable Universal Credit income"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        has_uc = benunit("universal_credit", period) > 0
        allowed_elements = add(
            benunit,
            period,
            [
                "uc_standard_allowance",
                "uc_child_element",
            ],
        )
        income_reduction = benunit("uc_income_reduction", period)
        return has_uc * max_(0, allowed_elements - income_reduction)
