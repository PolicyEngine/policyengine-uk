from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    local_non_dep_deductions,
)


class arun_council_tax_reduction_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "Arun Council Tax Reduction non-dependant deductions"
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.arun.gov.uk/download.cfm?doc=docm93jijm4n20657.pdf&ver=27819"
    )

    def formula(benunit, period, parameters):
        return local_non_dep_deductions(
            benunit,
            period,
            "arun_council_tax_reduction_individual_non_dep_deduction",
        )
