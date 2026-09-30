from policyengine_uk.model_api import *


class housing_benefit_pension_age_regulations_apply(Variable):
    value_type = bool
    entity = BenUnit
    label = "Housing Benefit falls under the pension-age regulations"
    documentation = (
        "Whether a Housing Benefit claim by this family falls under the Housing "
        "Benefit (Persons who have attained the qualifying age for state "
        "pension credit) Regulations 2006 rather than the Housing Benefit "
        "Regulations 2006. That is the case where the claimant or partner has "
        "reached the qualifying age for State Pension Credit and neither of "
        "them is on Universal Credit, Income Support, income-based Jobseeker's "
        "Allowance or income-related Employment and Support Allowance. The "
        "benefit cap (Part 8A of the working-age regulations) does not reach "
        "Housing Benefit under the pension-age regulations."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/5",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/5",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/5",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        # Every member stands in for the claimant and partner, and is_SP_age
        # for the qualifying age for State Pension Credit, as elsewhere in the
        # model.
        attained_qualifying_age = benunit.any(person("is_SP_age", period))
        # The Universal Credit award is read before the benefit cap, which
        # depends on this variable.
        on_universal_credit = benunit("is_uc_entitled", period)
        on_income_related_benefit = (
            add(benunit, period, ["income_support", "jsa_income", "esa_income"]) > 0
        )
        return (
            attained_qualifying_age & ~on_universal_credit & ~on_income_related_benefit
        )
