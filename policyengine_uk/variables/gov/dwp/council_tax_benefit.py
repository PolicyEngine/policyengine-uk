from policyengine_uk.model_api import *


class council_tax_benefit(Variable):
    value_type = float
    entity = BenUnit
    label = "Council Tax Benefit"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        supported = benunit.household("council_tax_reduction_scheme_supported", period)
        simulated = benunit("simulated_council_tax_reduction_benunit", period)
        reported = benunit("council_tax_benefit_reported", period)
        return where(supported, simulated, reported)
