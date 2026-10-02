from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.esa_income import income_related_esa_award
from policyengine_uk.variables.gov.dwp.jsa_income import income_related_jsa_award


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
        "or a single claimant with a child placed by a local authority), not "
        "be engaged in remunerative work (16 hours a week or more, unless a "
        "carer) and not be entitled to Employment and Support Allowance or "
        "Jobseeker's Allowance. The partner must not be engaged in "
        "remunerative work (24 hours a week or more, unless a carer). Neither "
        "the claimant nor the partner may be entitled to income-related ESA "
        "or income-based JSA. An adult in the benefit unit who is neither the "
        "claimant nor the partner (such as a non-dependent adult) does not "
        "affect eligibility, with a declared exception for a stored "
        "esa_income or jsa_income that is not the formula's own result. "
        "Whether entered directly or replaced by a reform (including one that "
        "scales it), such a value is read through the reported awards when it "
        "equals what they give (the award after the benefit's screen, or "
        "their plain total, to within half a penny after rounding to the "
        "precision it is stored in), and is otherwise taken to be the "
        "claimant's or partner's. So another member's report can change how "
        "such a value is read. A stored award of zero never bars the claim."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/124",
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/4ZA",
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/5",
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/6",
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
        # placed" by a local authority or voluntary organisation. A child is
        # under 16 (SSCBA s.137(1)). The model's proxy is a member under 16
        # flagged is_looked_after_by_local_authority; the flag also marks a
        # child living away in a local authority's care, whom para 2 does not
        # cover, and the model cannot tell the two apart. Para 4 is a carer.
        youngest_child_5_or_under = (
            benunit("youngest_child_age_for_legacy_benefits", period)
            <= IS.eligibility.lone_parent_youngest_child_age_limit
        )
        lone_parent_with_young_child = (
            benunit("is_lone_parent", period) & youngest_child_5_or_under
        )
        placed_child = (
            person("is_looked_after_by_local_authority", period)
            & person("is_child_for_child_benefit", period)
            & ~claimant_or_partner
        )
        single_with_placed_child = benunit("is_single", period) & benunit.any(
            placed_child
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
        # s.124(1)(c): neither the claimant nor the other member of a couple
        # is engaged in remunerative work: paid work of at least 16 hours a
        # week for the claimant (IS Regs 1987 reg 5(1)) and 24 for the
        # partner (reg 5(1A)). A person to whom Sch 1B para 4 applies, a carer,
        # is not treated as engaged in it, whether claimant or partner
        # (reg 6(4)(c)). The partner's threshold applies to whoever is not
        # the claimant, so it is tested for each candidate claimant against
        # the other member of the couple.
        WORK = IS.eligibility.remunerative_work
        hours = person("income_support_remunerative_work_hours", period)
        not_treated_as_working = person("is_carer_for_benefits", period)
        works_as_claimant = ~not_treated_as_working & (hours >= WORK.claimant_hours)
        works_as_partner = (
            claimant_or_partner
            & ~not_treated_as_working
            & (hours >= WORK.partner_hours)
        )
        other_member_works = (
            benunit.project(benunit.sum(works_as_partner)) - works_as_partner
        ) > 0
        # s.124(1)(f): the claimant is not entitled to a jobseeker's allowance
        # of either kind. Income-based JSA is tested below for both of them.
        no_contributory_jsa = person("jsa_contrib", period) <= 0
        # s.124(1)(h): the claimant is not entitled to an employment and
        # support allowance of either kind ...
        no_contributory_esa = person("esa_contrib", period) <= 0
        claimant = (
            has_award
            & prescribed_category
            & under_qualifying_age
            & no_contributory_esa
            & no_contributory_jsa
            & ~works_as_claimant
            & ~other_member_works
        )
        # ... and the other member of a couple is not entitled to an
        # income-related allowance. An income-related allowance covers the
        # couple, so it bars Income Support whichever of them has it: the
        # award on the claimant's and partner's reported amounts, after the
        # same screen as esa_income (esa_income_eligible). When esa_income
        # holds what the reported amounts give, either after that screen (the
        # formula) or as their plain total (the disable_simulated_benefits
        # reform), the reports say whose award it is. When it holds anything
        # else (an award entered directly, or a reform that replaces, scales
        # or removes it), they do not, and it is taken to be the claimant's
        # or partner's. A stored value equal to either amount, to within half
        # a penny after rounding to its stored precision, is read through the
        # reports. Either way, no income-related ESA is paid when esa_income
        # is zero, so a zero never bars the claim.
        esa_income = benunit("esa_income", period)
        reported_total = add(benunit, period, ["esa_income_reported"])
        award_on_all_reports = income_related_esa_award(benunit, period, reported_total)
        award_on_claimant_or_partner_reports = income_related_esa_award(
            benunit,
            period,
            benunit.sum(person("esa_income_reported", period) * claimant_or_partner),
        )
        # Compare in the precision esa_income is stored in (float32), so the
        # formula's own award always matches the award recomputed here.
        stored = esa_income.dtype
        as_reported = np.isclose(
            esa_income, award_on_all_reports.astype(stored), rtol=0, atol=0.005
        ) | np.isclose(esa_income, reported_total.astype(stored), rtol=0, atol=0.005)
        income_related_esa = (esa_income > 0) & (
            ~as_reported | (award_on_claimant_or_partner_reports > 0)
        )
        # s.124(1)(f): neither the claimant nor the other member of a couple
        # is, and the couple are not, entitled to an income-based jobseeker's
        # allowance, read the same way: the award on the claimant's and
        # partner's reported amounts after the screen jsa_income applies
        # (jsa_income_eligible), unless jsa_income holds something the
        # reported amounts do not give.
        jsa_income = benunit("jsa_income", period)
        jsa_reported_total = add(benunit, period, ["jsa_income_reported"])
        jsa_award_on_all_reports = income_related_jsa_award(
            benunit, period, jsa_reported_total
        )
        jsa_award_on_claimant_or_partner_reports = income_related_jsa_award(
            benunit,
            period,
            benunit.sum(person("jsa_income_reported", period) * claimant_or_partner),
        )
        # Compare in the stored award's precision: the holder keeps it as
        # float32, while the sums are float64.
        jsa_as_reported = np.isclose(
            jsa_income,
            jsa_award_on_all_reports.astype(jsa_income.dtype),
            rtol=0,
            atol=0.005,
        ) | np.isclose(
            jsa_income, jsa_reported_total.astype(jsa_income.dtype), rtol=0, atol=0.005
        )
        # As for ESA, a stored award of zero never bars the claim, even when
        # it is within half a penny of a sub-penny award on the reports.
        income_based_jsa = (jsa_income > 0) & (
            ~jsa_as_reported | (jsa_award_on_claimant_or_partner_reports > 0)
        )
        capital = benunit("income_support_assessable_capital", period)
        return (
            benunit.any(claimant)
            & ~income_related_esa
            & ~income_based_jsa
            & (capital <= IS.means_test.capital.limit)
        )
