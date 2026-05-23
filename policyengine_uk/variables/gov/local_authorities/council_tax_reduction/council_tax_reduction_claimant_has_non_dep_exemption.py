from policyengine_uk.model_api import *


class council_tax_reduction_claimant_has_non_dep_exemption(Variable):
    value_type = bool
    entity = BenUnit
    label = "CTR claimant has Dudley non-dependant deduction exemption"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        pip_daily_living = benunit.any(benunit.members("pip_dl", period) > 0)
        dla_care = benunit.any(benunit.members("dla_sc", period) > 0)
        return pip_daily_living | dla_care
