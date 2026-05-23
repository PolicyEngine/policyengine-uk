from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    local_non_dep_deductions,
)


class forest_of_dean_council_tax_reduction_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "Forest of Dean Council Tax Support non-dependant deductions"
    documentation = "Section 58 uses the prescribed Default Scheme gross-income non-dependant deduction schedule, with paragraph 58.3 applying the one-deduction couple rule to all couples (no Universal Credit carve-out, in contrast to the prescribed Default Scheme paragraph 30(3))."
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        return local_non_dep_deductions(
            benunit,
            period,
            "forest_of_dean_council_tax_reduction_individual_non_dep_deduction",
            one_deduction_for_uc_couples=True,
        )
