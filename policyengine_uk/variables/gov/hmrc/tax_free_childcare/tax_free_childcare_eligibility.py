from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.hmrc.tax_free_childcare._top_up import (
    meets_tax_free_childcare_family_conditions,
)


class tax_free_childcare_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "overall eligibility for tax-free childcare"
    definition_period = YEAR
    defined_for = "would_claim_tfc"

    def formula(benunit, period, parameters):
        childcare_eligible = benunit("tax_free_childcare_program_eligible", period)
        return np.logical_and(
            meets_tax_free_childcare_family_conditions(benunit, period),
            childcare_eligible,
        )
