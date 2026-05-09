from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    local_non_dep_deductions,
)


class derby_council_tax_reduction_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "Derby Council Tax Support non-dependant deductions"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.derby.gov.uk/media/derbycitycouncil/contentassets/documents/adviceandbenefits/counciltax/council-tax-support-scheme2026-27.pdf"

    def formula(benunit, period, parameters):
        return local_non_dep_deductions(
            benunit,
            period,
            "derby_council_tax_reduction_individual_non_dep_deduction",
        )
