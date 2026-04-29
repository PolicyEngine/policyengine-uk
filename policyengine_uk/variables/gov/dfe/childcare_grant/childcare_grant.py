from policyengine_uk.model_api import *


class childcare_grant(Variable):
    value_type = float
    entity = Person
    label = "Childcare Grant"
    documentation = (
        "Student Finance England Childcare Grant for full-time undergraduates with dependent children. "
        "The model reimburses 85% of annual out-of-pocket childcare expenses, capped by the official "
        "weekly maxima. `childcare_expenses` should therefore exclude any hours already covered by free "
        "childcare entitlements."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "childcare_grant_eligible"

    def formula(person, period, parameters):
        p = parameters(period).gov.dfe.childcare_grant
        eligible_children = person.benunit("childcare_grant_eligible_children", period)
        childcare_expenses = person("childcare_expenses", period)

        weekly_cap = where(
            eligible_children == 1,
            p.weekly_maximum.one_child,
            p.weekly_maximum.two_or_more_children,
        )
        annual_cap = weekly_cap * WEEKS_IN_YEAR
        covered_expenses = childcare_expenses * p.coverage_rate
        return min_(covered_expenses, annual_cap)
