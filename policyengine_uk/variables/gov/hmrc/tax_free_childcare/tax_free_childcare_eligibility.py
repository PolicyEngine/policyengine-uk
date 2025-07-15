from policyengine_uk.model_api import *


class tax_free_childcare_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "overall eligibility for tax-free childcare"
    definition_period = YEAR
    defined_for = "would_claim_tfc"

    def formula(benunit, period, parameters):
        meets_age_condition = benunit.any(
            benunit.members("tax_free_childcare_child_age_eligible", period),
        )

        meets_income_condition = benunit.all(
            benunit.members(
                "tax_free_childcare_meets_income_requirements", period
            )
            | ~benunit.members("is_parent", period)
        )

        childcare_eligible = benunit(
            "tax_free_childcare_program_eligible", period
        )

        work_eligible = benunit("tax_free_childcare_work_condition", period)

        return np.logical_and.reduce(
            [
                meets_age_condition,
                meets_income_condition,
                childcare_eligible,
                work_eligible,
            ]
        )
