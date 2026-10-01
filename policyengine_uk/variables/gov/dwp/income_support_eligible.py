from policyengine_uk.model_api import *


class income_support_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether eligible for Income Support"
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/1B",
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/4ZA",
        "https://www.legislation.gov.uk/ukpga/1992/4/section/124",
        "https://www.legislation.gov.uk/uksi/1987/1968/regulation/4",
    )

    def formula(benunit, period, parameters):
        IS = parameters(period).gov.dwp.income_support
        # Schedule 1B para 1 says "under 5". Retain the existing inclusive
        # comparison pending a separate decision on the annual-age model.
        youngest_child_5_or_under = (
            benunit("youngest_child_age_for_legacy_benefits", period)
            <= IS.eligibility.lone_parent_youngest_child_age_limit
        )
        lone_parent = benunit("is_lone_parent", period)
        lone_parent_with_young_child = lone_parent & youngest_child_5_or_under
        # Sch 1B para 4 prescribes the carer, and SSCBA s.124(1)(e) requires
        # the claimant to fall within a prescribed category. A couple choose
        # which of them claims (Claims and Payments Regs 1987 reg 4(3)), so
        # either partner's caring qualifies; a child's or young person's
        # caring does not.
        claimant_or_partner = benunit.members("is_claimant_or_partner", period)
        carer = benunit.members("is_carer_for_benefits", period)
        claimant_or_partner_cares = benunit.any(claimant_or_partner & carer)
        none_SP_age = ~benunit.any(benunit.members("is_SP_age", period))
        has_esa_income = benunit("esa_income", period) > 0
        already_claiming = add(benunit, period, ["income_support_reported"]) > 0
        capital = benunit("income_support_assessable_capital", period)
        limit = IS.means_test.capital.limit
        return (
            (claimant_or_partner_cares | lone_parent_with_young_child)
            & none_SP_age
            & ~has_esa_income
            & already_claiming
            & (capital <= limit)
        )
