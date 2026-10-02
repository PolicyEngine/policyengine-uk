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
        "Housing Benefit under the pension-age regulations. A Universal Credit "
        "award counts only where a claimant or partner is under the qualifying "
        "age. That is right for the cap, which SI 2014/1230 reg 60C disapplies "
        "for a claim where every claimant has reached that age, but not for "
        "reg 5 itself, under which such an award would bring in the "
        "working-age regulations. The model has no lawful such awards (tax "
        "credit migrants under SI 2014/1230 reg 60A are not modelled); the "
        "ones it pays through is_uc_eligible's any-adult test are not awards "
        "in law, so the pension-age regulations are the right result."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/5",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/5",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/5",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        claimant_or_partner = person("is_uc_claimant", period)
        # is_SP_age stands in for the qualifying age for State Pension Credit,
        # as elsewhere in the model.
        over_qualifying_age = person("is_SP_age", period)
        attained_qualifying_age = benunit.any(claimant_or_partner & over_qualifying_age)
        # Universal Credit needs a claimant or partner under the qualifying age
        # (WRA 2012 s.4(1)(b); UC Regs 2013 reg 3(2)(a)), except for tax credit
        # migrants (SI 2014/1230 reg 60A), whose award is exempt from the cap
        # (reg 60C). is_uc_eligible counts any working-age adult, so the model
        # can pay Universal Credit to a pensioner whose only younger adult is
        # a qualifying young person; that award does not take the family out
        # of the pension-age rules. is_uc_claimant recognises the young person
        # as a dependant only when is_parent is set, as in the FRS datasets.
        # The award is read before the benefit cap, which depends on this
        # variable.
        working_age_claimant = benunit.any(claimant_or_partner & ~over_qualifying_age)
        on_universal_credit = benunit("is_uc_entitled", period) & working_age_claimant
        # Reg 5(1)(b) asks whether the claimant or partner is on one of these
        # awards. Income Support already needs their own award
        # (income_support_eligible); income-based JSA and income-related ESA
        # are read on their reports only, since another member of the benefit
        # unit claims in their own right.
        on_income_related_benefit = (
            add(
                benunit,
                period,
                [
                    "income_support",
                    "claimant_or_partner_jsa_income",
                    "claimant_or_partner_esa_income",
                ],
            )
            > 0
        )
        return (
            attained_qualifying_age & ~on_universal_credit & ~on_income_related_benefit
        )
