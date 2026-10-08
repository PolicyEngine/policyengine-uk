from policyengine_uk.model_api import *


class council_tax_reduction_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "Pensioner for Council Tax Reduction"
    documentation = (
        "Whether this family's claim falls under the pension-age Council Tax "
        "Reduction rules: the applicant or the applicant's partner has reached "
        "the qualifying age for State Pension Credit, and neither of them is "
        "on Income Support, income-based Jobseeker's Allowance or "
        "income-related Employment and Support Allowance, or has an award of "
        "Universal Credit. A mixed-age couple on Universal Credit is therefore "
        "not a pensioner in England, Wales or Scotland. Each applicant's "
        "scheme follows their own family, so where families share the rent "
        "and each claims, a working-age family is assessed under the "
        "working-age rules even if the household head's family is "
        "pension-age, and the reverse. The shared applicable allowance uses "
        "this test, as does English scheme selection; Welsh and Scottish "
        "scheme selection retains its existing approximations."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/3",
        "https://www.legislation.gov.uk/uksi/2012/2886/schedule/paragraph/3",
        "https://www.legislation.gov.uk/wsi/2013/3029/regulation/3",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/3",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/12",
        "https://www.legislation.gov.uk/ssi/2012/303/regulation/12",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        # The applicant and partner whose claim this is
        # (is_council_tax_reduction_applicant_or_partner), not the household
        # head's family.
        applicant_or_partner = person(
            "is_council_tax_reduction_applicant_or_partner", period
        )
        # Either member of a couple can claim, so the older one can claim as a
        # pensioner: "has attained the qualifying age for state pension credit"
        # (SI 2012/2885 reg 3(1)(a)(i), WSI 2013/3029 reg 3(1)(a)(i),
        # SSI 2012/319 reg 12(1)). The benefit conditions still apply.
        over_qualifying_age = person(
            "has_attained_state_pension_credit_qualifying_age", period
        )
        attained_qualifying_age = benunit.any(
            applicant_or_partner & over_qualifying_age
        )
        # The benefit unit's Income Support, income-based JSA, income-related
        # ESA and Universal Credit belong to its claimant and partner. Where
        # the household head applies alone, they are not the applicant's.
        head_applies_alone = benunit("council_tax_reduction_head_applies_alone", period)
        income_related_benefit = (
            benunit("council_tax_reduction_relevant_income_based_benefit", period)
            & ~head_applies_alone
        )
        # The award before the benefit cap: the cap reduces an award
        # (UC Regs 2013 reg 81) rather than removing it. An award counts only
        # where the applicant or partner is under the qualifying age, which
        # Universal Credit needs (UC Regs 2013 reg 3(2)(a)). A dependant is
        # neither: outside a head who applies alone, the applicant and partner
        # are the benefit unit's claimant and partner, and
        # is_claimant_or_partner presumes a member under 20 and at least 16
        # years younger than the claimant to be their child, so a pensioner's
        # 18- or 19-year-old does not count, whether or not is_parent
        # identifies the pensioner as the parent.
        # This also stands in for the rules that disregard an award held after
        # both members reach the qualifying age (SI 2012/2885 reg 3(2);
        # WSI 2013/3029 reg 3(2); SSI 2021/249 reg 3(2)). England, and Wales
        # for schemes from 2026-27, also disregard a tax credit migrant's award
        # (UC (TP) Regs 2014 reg 60A) and Scotland does not; the model does not
        # model those migrants.
        working_age_applicant = benunit.any(applicant_or_partner & ~over_qualifying_age)
        universal_credit_award = (
            benunit("is_uc_entitled", period)
            & ~head_applies_alone
            & working_age_applicant
        )
        return (
            attained_qualifying_age & ~income_related_benefit & ~universal_credit_award
        )
