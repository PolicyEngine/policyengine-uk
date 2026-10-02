from policyengine_uk.model_api import *


class income_support_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether eligible for Income Support"
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/1B",
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/1B/paragraph/2",
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/1B/paragraph/2A",
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
        # Schedule 1B para 2: a single claimant or lone parent with whom a
        # child is placed by a local authority, such as a foster child; para
        # 2A: or placed for adoption by an adoption agency.
        person = benunit.members
        placed_child = person(
            "is_child_or_young_person_placed_with_family", period
        ) & person("is_child_for_child_benefit", period)
        single_or_lone_parent = benunit("is_single_person", period) | lone_parent
        has_placed_child = single_or_lone_parent & benunit.any(placed_child)
        has_carers = add(benunit, period, ["is_carer_for_benefits"]) > 0
        none_SP_age = ~benunit.any(benunit.members("is_SP_age", period))
        has_esa_income = benunit("esa_income", period) > 0
        already_claiming = add(benunit, period, ["income_support_reported"]) > 0
        capital = benunit("income_support_assessable_capital", period)
        limit = IS.means_test.capital.limit
        return (
            (has_carers | lone_parent_with_young_child | has_placed_child)
            & none_SP_age
            & ~has_esa_income
            & already_claiming
            & (capital <= limit)
        )
