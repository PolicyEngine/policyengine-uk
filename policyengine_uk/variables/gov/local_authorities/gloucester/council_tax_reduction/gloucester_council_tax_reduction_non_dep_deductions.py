from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    local_non_dep_deductions,
)


class gloucester_council_tax_reduction_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "Gloucester Council Tax Support non-dependant deductions"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.gloucester.gov.uk/media/ruwinppa/local-council-tax-support-policy-2026-v2.pdf"

    def formula(benunit, period, parameters):
        return local_non_dep_deductions(
            benunit,
            period,
            "gloucester_council_tax_reduction_individual_non_dep_deduction",
            one_deduction_for_uc_couples=False,
        )
