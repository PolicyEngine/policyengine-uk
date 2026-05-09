from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    local_non_dep_deductions,
)


class bassetlaw_council_tax_reduction_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "Bassetlaw Council Tax Reduction non-dependant deductions"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.bassetlaw.gov.uk/media/15ehht0s/council-tax-reduction-scheme-working-age-2026-2027.pdf"

    def formula(benunit, period, parameters):
        return local_non_dep_deductions(
            benunit,
            period,
            "bassetlaw_council_tax_reduction_individual_non_dep_deduction",
            one_deduction_for_uc_couples=False,
        )
