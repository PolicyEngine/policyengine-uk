from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    local_non_dep_deductions,
)


class kingston_upon_hull_council_tax_reduction_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "Kingston upon Hull Council Tax Reduction non-dependant deductions"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        return local_non_dep_deductions(
            benunit,
            period,
            "kingston_upon_hull_council_tax_reduction_individual_non_dep_deduction",
        )
