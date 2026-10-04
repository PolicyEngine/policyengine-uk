from policyengine_uk.model_api import *


class income_support_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether eligible for Income Support"
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/1B",
        "https://www.legislation.gov.uk/ukpga/1992/4/section/124",
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
        has_carers = add(benunit, period, ["is_carer_for_benefits"]) > 0
        # SSCBA 1992 s.124(1)(aa): the claimant has not attained the qualifying
        # age for State Pension Credit. Either member of a couple can claim, so
        # a mixed-age couple can claim through the younger one.
        person = benunit.members
        claimant_under_qualifying_age = benunit.any(
            person("is_claimant_or_partner", period)
            & ~person("has_attained_state_pension_credit_qualifying_age", period)
        )
        # s.124(1)(g): the other member of a couple is not entitled to State
        # Pension Credit. Entitlement needs a claim (SSAA 1992 s.1). Reading the
        # Pension Credit amount here would be circular (Pension Credit income
        # counts working tax credit, whose income counts Income Support), so a
        # couple is taken to be on Pension Credit where it meets the Pension
        # Credit age conditions and would claim it. That leaves out Pension
        # Credit's means test: a couple whose income is too high for Pension
        # Credit is treated as on it, which bars an Income Support award only
        # where its income is below the lower Income Support applicable amount.
        on_pension_credit = benunit(
            "meets_pension_credit_age_conditions", period
        ) & benunit("would_claim_pc", period)
        has_esa_income = benunit("esa_income", period) > 0
        already_claiming = add(benunit, period, ["income_support_reported"]) > 0
        capital = benunit("income_support_assessable_capital", period)
        limit = IS.means_test.capital.limit
        return (
            (has_carers | lone_parent_with_young_child)
            & claimant_under_qualifying_age
            & ~on_pension_credit
            & ~has_esa_income
            & already_claiming
            & (capital <= limit)
        )
