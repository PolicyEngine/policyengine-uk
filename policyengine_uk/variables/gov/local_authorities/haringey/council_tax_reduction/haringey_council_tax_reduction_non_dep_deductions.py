from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    local_non_dep_deductions,
)


class haringey_council_tax_reduction_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "Haringey CTR non-dependent deductions"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        return local_non_dep_deductions(
            benunit,
            period,
            "haringey_council_tax_reduction_individual_non_dep_deduction",
            one_deduction_for_uc_couples=False,
        )
