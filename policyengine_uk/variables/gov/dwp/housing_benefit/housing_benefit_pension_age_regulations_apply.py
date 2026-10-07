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
        "credit migrants under SI 2014/1230 reg 60A are not modelled), and its "
        "Universal Credit eligibility test also needs a claimant or partner "
        "under the qualifying age, so the pension-age regulations are the right "
        "result."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/5",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/5",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/5",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        claimant_or_partner = person("is_claimant_or_partner", period)
        # HB (SPC) Regs 2006 reg 5(1): "has attained the qualifying age for
        # state pension credit"; reg 5(2) excludes the benefits below.
        over_qualifying_age = person(
            "has_attained_state_pension_credit_qualifying_age", period
        )
        attained_qualifying_age = benunit.any(claimant_or_partner & over_qualifying_age)
        # Universal Credit needs a claimant or partner under the qualifying age
        # (WRA 2012 s.4(1)(b); UC Regs 2013 reg 3(2)(a)), except for tax credit
        # migrants (SI 2014/1230 reg 60A), whose award is exempt from the cap
        # (reg 60C). An award counts here only with such a claimant or partner.
        # A dependant is neither: is_claimant_or_partner presumes a member under
        # 20 and at least 16 years younger than the claimant to be their child,
        # so a pensioner's 18- or 19-year-old does not make the award a
        # working-age one, whether or not is_parent identifies the pensioner as
        # the parent. The award is read before the benefit cap, which depends
        # on this variable.
        working_age_claimant = benunit.any(claimant_or_partner & ~over_qualifying_age)
        on_universal_credit = benunit("is_uc_entitled", period) & working_age_claimant
        # Reg 5 names the same three benefits as the CTR pensioner test.
        on_income_related_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        return (
            attained_qualifying_age & ~on_universal_credit & ~on_income_related_benefit
        )
