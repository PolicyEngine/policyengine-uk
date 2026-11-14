from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.hmrc.tax_free_childcare._top_up import (
    UNIVERSAL_CREDIT_AWARDS,
    meets_tax_free_childcare_family_conditions,
)

# The reported receipt each tax credit award continues from (is_CTC_eligible,
# is_WTC_eligible).
TAX_CREDIT_REPORTS = {
    "child_tax_credit": "child_tax_credit_reported",
    "working_tax_credit": "working_tax_credit_reported",
}


class tax_free_childcare_eligible_without_universal_credit(Variable):
    value_type = bool
    entity = BenUnit
    label = "eligible for Tax-Free Childcare without a Universal Credit claim"
    documentation = (
        "Whether the family would be eligible for Tax-Free Childcare if it "
        "did not claim Universal Credit: tax_free_childcare_eligible with "
        "every disqualifying programme counted except Universal Credit. A "
        "tax credit counts while the family receives it and DWP has not "
        "closed it, as for the award itself; its amount is not read, since "
        "it counts Pension Credit, which reads Universal Credit. "
        "forgoes_universal_credit_for_tax_free_childcare compares the "
        "top-up this gives with the Universal Credit award."
    )
    definition_period = YEAR
    defined_for = "would_claim_tfc"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2014/28/section/11",
        "https://www.legislation.gov.uk/ukpga/2014/28/section/30",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.hmrc.tax_free_childcare
        programs = [
            program
            for program in p.disqualifying_benefits
            if program not in UNIVERSAL_CREDIT_AWARDS
        ]
        reports = [TAX_CREDIT_REPORTS[x] for x in programs if x in TAX_CREDIT_REPORTS]
        others = [x for x in programs if x not in TAX_CREDIT_REPORTS]
        none = np.zeros(benunit.count, dtype=bool)
        on_tax_credits = (
            (add(benunit, period, reports) > 0)
            & ~benunit("legacy_benefits_closed", period)
            if reports
            else none
        )
        on_other_program = add(benunit, period, others) > 0 if others else none
        return np.logical_and.reduce(
            [
                meets_tax_free_childcare_family_conditions(benunit, period),
                ~on_tax_credits,
                ~on_other_program,
                benunit("tax_free_childcare_meets_uk_connection", period),
            ]
        )
