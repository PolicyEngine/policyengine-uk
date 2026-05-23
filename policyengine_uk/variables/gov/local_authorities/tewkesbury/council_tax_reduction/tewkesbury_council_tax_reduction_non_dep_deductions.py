from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    local_non_dep_deductions,
)


class tewkesbury_council_tax_reduction_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "Tewkesbury Council Tax Reduction non-dependant deductions"
    documentation = "Tewkesbury follows the Default Scheme paragraph 30 schedule of weekly gross-income non-dependant deductions, as amended by SI 2012/3085. Paragraph 30(3) excludes Universal Credit non-dependant couples from the one-deduction couple rule, so each UC member of a non-dependant couple counts separately."
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        return local_non_dep_deductions(
            benunit,
            period,
            "tewkesbury_council_tax_reduction_individual_non_dep_deduction",
            one_deduction_for_uc_couples=False,
        )
