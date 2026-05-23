from policyengine_uk.model_api import *


class hillingdon_council_tax_reduction_countable_universal_credit(Variable):
    value_type = float
    entity = BenUnit
    label = "Hillingdon CTR countable Universal Credit income"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ignored_elements = add(
            benunit,
            period,
            [
                "uc_housing_costs_element",
                "uc_childcare_element",
                "uc_disability_elements",
                "uc_carer_element",
            ],
        )
        has_uc = benunit("universal_credit", period) > 0
        return has_uc * max_(0, benunit("universal_credit", period) - ignored_elements)
