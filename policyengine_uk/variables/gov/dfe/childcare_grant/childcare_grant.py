from policyengine_uk.model_api import *


class childcare_grant(Variable):
    value_type = float
    entity = Person
    label = "Childcare Grant"
    documentation = (
        "Student Finance England Childcare Grant for full-time undergraduates "
        "with dependent children. The model aggregates nonnegative annual "
        "childcare_expenses on eligible children in the benefit unit, applies "
        "the coverage rate and caps the family award at 52 weekly maxima. "
        "The weekly cap and income limit count all age-eligible dependent "
        "children, including those with no childcare expenses. SLC guidance "
        "bases its maximum on children declared as requiring childcare; that "
        "application-based count is not represented by this convention. "
        "Expenses must exclude hours covered by free childcare entitlements. "
        "The model allocates the family award to the eldest eligible student "
        "parent; this is an allocation convention, as actual awards can be "
        "split between eligible student partners."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "childcare_grant_eligible"
    reference = (
        "https://www.legislation.gov.uk/uksi/2011/1986/regulation/45",
        "https://www.legislation.gov.uk/uksi/2011/1986/regulation/47",
        "https://www.practitioners.slc.co.uk/media/2156/sfe-grants-for-dependants-ay2627-v30.pdf#page=33",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dfe.childcare_grant
        eligible_children = person.benunit("childcare_grant_eligible_children", period)
        eligible_child = person("childcare_grant_child_eligible", period)
        child_costs = max_(person("childcare_expenses", period), 0)
        childcare_expenses = person.benunit.sum(where(eligible_child, child_costs, 0))

        weekly_cap = where(
            eligible_children == 1,
            p.weekly_maximum.one_child,
            p.weekly_maximum.two_or_more_children,
        )
        annual_cap = weekly_cap * WEEKS_IN_YEAR
        covered_expenses = childcare_expenses * p.coverage_rate
        family_award = min_(covered_expenses, annual_cap)
        eligible_parent = person("childcare_grant_eligible", period)
        receives_family_award = (
            person.get_rank(
                person.benunit, -person("age", period), condition=eligible_parent
            )
            == 0
        )
        return where(receives_family_award, family_award, 0)
