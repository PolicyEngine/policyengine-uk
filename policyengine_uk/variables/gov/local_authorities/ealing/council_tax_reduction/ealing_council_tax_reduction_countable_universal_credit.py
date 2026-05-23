from policyengine_uk.model_api import *


class ealing_council_tax_reduction_countable_universal_credit(Variable):
    value_type = float
    entity = BenUnit
    label = "Ealing CTR countable Universal Credit income"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        has_uc = benunit("universal_credit", period) > 0
        assessed_income = add(
            benunit,
            period,
            [
                "uc_earned_income",
                "uc_unearned_income",
            ],
        )
        return has_uc * assessed_income
