from policyengine_uk.model_api import *


class care_to_learn(Variable):
    value_type = float
    entity = Person
    label = "Care to Learn scheme amount"
    documentation = (
        "Care to Learn pays a young parent's childcare costs, and any extra "
        "travel between home and the childcare provider, up to a weekly "
        "maximum per child (ESFA conditions of grant, sections 2.2 and 4.1). "
        "The model caps each qualifying child's annual childcare_expenses at "
        "52 weeks of that maximum; it does not model the travel costs. Only "
        "one parent can claim for a child, so the benefit unit's total is "
        "paid to one eligible young parent, the eldest."
    )
    definition_period = YEAR
    quantity_type = FLOW
    unit = GBP
    default_value = 0
    defined_for = "care_to_learn_eligible"
    reference = (
        "https://www.gov.uk/government/publications/care-to-learn-conditions-of-grant-funding/care-to-learn-academic-year-2026-to-2027-conditions-of-grant-funding",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dfe.care_to_learn.amount
        # London weighting follows the young parent's home address.
        region = person.household("region", period)
        weekly_maximum_per_child = where(
            region == region.possible_values.LONDON,
            p.in_london,
            p.outside_london,
        )
        qualifying_child = person("care_to_learn_qualifying_child", period)
        childcare_costs = max_(person("childcare_expenses", period), 0)
        amount_per_child = qualifying_child * min_(
            childcare_costs, weekly_maximum_per_child * WEEKS_IN_YEAR
        )
        benunit_amount = person.benunit.sum(amount_per_child)

        eligible = person("care_to_learn_eligible", period)
        claims_for_benunit = (
            person.get_rank(person.benunit, -person("age", period), condition=eligible)
            == 0
        )
        return where(claims_for_benunit, benunit_amount, 0)
