from policyengine_uk.model_api import *


class camden_council_tax_reduction_protected_group(Variable):
    value_type = bool
    entity = BenUnit
    label = "Camden CTR disabled or carer group"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        person = benunit.members
        claimant_or_partner = person("is_adult", period)
        disability_or_carer_benefit = (
            (person("pip_dl", period) > 0)
            | (person("dla_sc", period) > 0)
            | (person("carers_allowance", period) > 0)
        )
        return benunit.any(claimant_or_partner & disability_or_carer_benefit)
