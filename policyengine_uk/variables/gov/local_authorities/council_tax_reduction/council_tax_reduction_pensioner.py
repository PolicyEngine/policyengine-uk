from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.country import Country


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
        "not a pensioner in England, Wales or Scotland. Wholly pension-age "
        "tax credit migrants whose upper UC age limit is waived under "
        "regulation 60A retain pensioner treatment in England from the "
        "2025-26 scheme year and Wales from 2026-27; Scotland treats their "
        "UC awards under the working-age rules. Other wholly pension-age "
        "UC input awards retain the model's approximation for an award "
        "awaiting termination or made in error. Each applicant's "
        "scheme follows their own family, so where families share the rent "
        "and each claims, a working-age family is assessed under the "
        "working-age rules even if the household head's family is "
        "pension-age, and the reverse. The shared applicable allowance uses "
        "this test, as does English scheme selection, the choice between the "
        "pensioner and working-age tariff income from capital, and the "
        "Scottish income rules; Welsh and Scottish award formulas retain "
        "their existing approximations."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/3",
        "https://www.legislation.gov.uk/uksi/2025/39/regulation/1",
        "https://www.legislation.gov.uk/uksi/2025/39/regulation/4",
        "https://www.legislation.gov.uk/uksi/2012/2886/schedule/paragraph/3",
        "https://www.legislation.gov.uk/wsi/2013/3029/regulation/3",
        "https://www.legislation.gov.uk/wsi/2026/13/regulation/1",
        "https://www.legislation.gov.uk/wsi/2026/13/regulation/4",
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
        # (UC Regs 2013 reg 81) rather than removing it. An ordinary award
        # counts where the applicant or partner is under the qualifying age
        # (UC Regs 2013 reg 3(2)(a)). A dependant is
        # neither: outside a head who applies alone, the applicant and partner
        # are the benefit unit's claimant and partner, and
        # is_claimant_or_partner presumes a member under 20 and at least 16
        # years younger than the claimant to be their child, so a pensioner's
        # 18- or 19-year-old does not count, whether or not is_parent
        # identifies the pensioner as the parent.
        working_age_applicant = benunit.any(applicant_or_partner & ~over_qualifying_age)
        # The model recognises reg 60A awards through the closure claim and
        # reported WTC. The waiver applies to a single pension-age claimant
        # or joint claimants both pension age, not mixed-age couples.
        pension_age_tax_credit_migrant = (
            benunit("claims_uc_at_legacy_closure", period)
            & (add(benunit, period, ["working_tax_credit_reported"]) > 0)
            & ~working_age_applicant
        )
        country = benunit.household("country", period)
        # Commencement alone does not determine the scheme: SI 2025/39
        # reg 1(3) applies from the financial year beginning April 2025;
        # WSI 2026/13 reg 1(3) from April 2026. Model years represent those
        # scheme years. SSI 2021/249 reg 3 has no reg 60A migrant exception.
        migrant_award_disregarded = (
            (country == Country.ENGLAND) & (period.start.year >= 2025)
        ) | ((country == Country.WALES) & (period.start.year >= 2026))
        # Other awards with no working-age applicant retain the existing
        # approximation for a final UC assessment-period run-on or an award
        # made in error (SI 2012/2885 reg 3(2); SSI 2021/249 reg 3(2)).
        universal_credit_award = (
            benunit("is_uc_entitled", period)
            & ~head_applies_alone
            & (
                working_age_applicant
                | (pension_age_tax_credit_migrant & ~migrant_award_disregarded)
            )
        )
        return (
            attained_qualifying_age & ~income_related_benefit & ~universal_credit_award
        )
