from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    local_non_dep_deductions,
)


class south_gloucestershire_council_tax_reduction_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "South Gloucestershire CTR non-dependant deductions"
    definition_period = YEAR
    unit = GBP
    reference = "https://beta.southglos.gov.uk/static/edf5960dd95611c375de976f8fa529cc/Council_tax_reduction_scheme_rules_working_age_applicants.pdf"

    def formula(benunit, period, parameters):
        return local_non_dep_deductions(
            benunit,
            period,
            "south_gloucestershire_council_tax_reduction_individual_non_dep_deduction",
        )
