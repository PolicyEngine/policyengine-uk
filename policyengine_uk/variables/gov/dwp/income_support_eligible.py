from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.esa_income import income_related_esa_award


class income_support_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether eligible for Income Support"
    documentation = (
        "SSCBA 1992 s.124(1) sets the conditions for the claimant and, for "
        "some of them, the claimant's partner. No new claims for Income "
        "Support can be made, and a partner who takes over an award makes a "
        "new claim, so the claimant is the one of the claimant and partner "
        "who has the existing award. The model takes that to be whichever of "
        "them reports Income Support (income_support_reported); if both do, "
        "either can be the claimant. The claimant must be under the "
        "qualifying age for State Pension Credit, fall within a prescribed "
        "category the model covers (a carer, a lone parent of a young child, "
        "or a single claimant with a child placed by a local authority) and "
        "not be entitled to Employment and Support Allowance. Neither the "
        "claimant nor the partner may be entitled to income-related ESA. An "
        "adult in the benefit unit who is neither the claimant nor the "
        "partner (such as a non-dependent adult) does not affect "
        "eligibility."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/124",
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/4ZA",
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/1B",
        "https://www.legislation.gov.uk/uksi/1987/1968/regulation/4",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/6A",
    )

    def formula(benunit, period, parameters):
        IS = parameters(period).gov.dwp.income_support
        person = benunit.members
        # SSCBA s.124(1) names the claimant and, in paras (c), (f), (g) and
        # (h), the other member of a couple; nobody else in the benefit unit.
        claimant_or_partner = person("is_claimant_or_partner", period)
        # No new claims for Income Support can be made (Universal Credit
        # (Transitional Provisions) Regs 2014 reg 6A(1)). A couple choose
        # which of them claims (Claims and Payments Regs 1987 reg 4(3)), but a
        # partner who takes over an award does so by claiming (reg 4(4)), so
        # the claimant is whichever of them has the existing award. The model
        # takes that to be the claimant or partner who reports Income Support.
        has_award = claimant_or_partner & (
            person("income_support_reported", period) > 0
        )
        # s.124(1)(e), reg 4ZA and Sch 1B: the claimant falls within a
        # prescribed category. The model covers three of them. Para 1 is a
        # lone parent responsible for a child under 5; Schedule 1B para 1
        # says "under 5", and the model retains the existing inclusive
        # comparison pending a separate decision on the annual-age model.
        # Para 2 is "a single claimant or a lone parent with whom a child is
        # placed" by a local authority or voluntary organisation; the model's
        # proxy is a member flagged is_looked_after_by_local_authority. Para 4
        # is a carer.
        youngest_child_5_or_under = (
            benunit("youngest_child_age_for_legacy_benefits", period)
            <= IS.eligibility.lone_parent_youngest_child_age_limit
        )
        lone_parent_with_young_child = (
            benunit("is_lone_parent", period) & youngest_child_5_or_under
        )
        single_with_placed_child = benunit("is_single", period) & benunit.any(
            person("is_looked_after_by_local_authority", period) & ~claimant_or_partner
        )
        prescribed_category = person("is_carer_for_benefits", period) | benunit.project(
            lone_parent_with_young_child | single_with_placed_child
        )
        # s.124(1)(aa): the claimant has not attained the qualifying age for
        # State Pension Credit, which is state pension age (SPCA 2002 s.1(6)).
        # A partner over that age does not bar the claim; s.124(1)(g) bars it
        # only if the partner is entitled to State Pension Credit, which a
        # mixed-age couple cannot be (SPCA 2002 s.4(1A); the SI 2019/37
        # art. 4 savings are not modelled, as in is_pension_credit_eligible).
        # Reading Pension Credit here would make a dependency cycle through
        # Working Tax Credit.
        under_qualifying_age = ~person("is_SP_age", period)
        # s.124(1)(h): the claimant is not entitled to an employment and
        # support allowance of either kind ...
        no_contributory_esa = person("esa_contrib", period) <= 0
        claimant = (
            has_award & prescribed_category & under_qualifying_age & no_contributory_esa
        )
        # ... and the other member of a couple is not entitled to an
        # income-related allowance. An income-related allowance covers the
        # couple, so it bars Income Support whichever of them has it: the
        # award on the claimant's and partner's reported amounts, after the
        # same screen as esa_income (esa_income_eligible). When esa_income
        # holds what the reported amounts give, either after that screen (the
        # formula) or as
        # their plain total (the disable_simulated_benefits reform), the
        # reports say whose award it is. When it holds anything else (an
        # award entered directly, or a reform that replaces or removes it),
        # they do not, and it is taken to be the claimant's or partner's. An
        # entered award equal to either amount is read through the reports.
        esa_income = benunit("esa_income", period)
        reported_total = add(benunit, period, ["esa_income_reported"])
        award_on_all_reports = income_related_esa_award(benunit, period, reported_total)
        award_on_claimant_or_partner_reports = income_related_esa_award(
            benunit,
            period,
            benunit.sum(person("esa_income_reported", period) * claimant_or_partner),
        )
        as_reported = np.isclose(
            esa_income, award_on_all_reports, rtol=0, atol=0.005
        ) | np.isclose(esa_income, reported_total, rtol=0, atol=0.005)
        income_related_esa = where(
            as_reported, award_on_claimant_or_partner_reports > 0, esa_income > 0
        )
        capital = benunit("income_support_assessable_capital", period)
        return (
            benunit.any(claimant)
            & ~income_related_esa
            & (capital <= IS.means_test.capital.limit)
        )
