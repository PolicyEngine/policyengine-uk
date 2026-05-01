from policyengine_uk.model_api import *


class enfield_council_tax_reduction_protected_group(Variable):
    value_type = bool
    entity = BenUnit
    label = "Enfield CTR working-age protected group"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        single_under_25 = benunit("is_single_person", period) & (
            benunit("eldest_adult_age", period) < 25
        )
        return single_under_25 | benunit(
            "enfield_council_tax_reduction_war_widow", period
        )
