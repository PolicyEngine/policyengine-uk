from policyengine_uk.model_api import *


class council_tax_reduction_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "Pensioner for Council Tax Reduction"
    documentation = (
        "Whether the family's claim falls under the pension-age Council Tax "
        "Reduction rules: the claimant has reached the qualifying age for "
        "State Pension Credit, and neither the claimant nor any partner is on "
        "Income Support, income-based Jobseeker's Allowance or income-related "
        "Employment and Support Allowance, or has an award of Universal Credit. "
        "A mixed-age couple on Universal Credit therefore claims under the "
        "working-age rules in England, Wales and Scotland."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/3",
        "https://www.legislation.gov.uk/wsi/2013/3029/regulation/3",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/12",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/3",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        # Any member can be the claimant (the older member of a couple claims),
        # and is_SP_age stands in for the qualifying age for State Pension
        # Credit, as elsewhere in the model.
        attained_qualifying_age = benunit.any(person("is_SP_age", period))
        income_related_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        # The award before the benefit cap: the cap reduces an award
        # (UC Regs 2013 reg 81) rather than removing it. The rules that
        # disregard an award held after both members reach the qualifying age
        # (SI 2012/2885 reg 3(2); SSI 2021/249 reg 3(2)) are not modelled:
        # Universal Credit here needs a working-age adult.
        universal_credit_award = benunit("is_uc_entitled", period)
        return (
            attained_qualifying_age & ~income_related_benefit & ~universal_credit_award
        )
