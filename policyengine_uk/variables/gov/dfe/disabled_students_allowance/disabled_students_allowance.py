from policyengine_uk.model_api import *


class disabled_students_allowance(Variable):
    value_type = float
    entity = Person
    label = "Disabled Students' Allowance"
    documentation = (
        "Student Finance England Disabled Students' Allowance. "
        "The published rules provide an annual cap, but actual awards depend on an "
        "individual needs assessment rather than a public formula. This first-pass "
        "model therefore treats `disabled_students_allowance_eligible_expenses` as "
        "the assessed annual study-related support need, net of any required personal "
        "computer contribution and excluding ordinary student costs."
    )
    definition_period = YEAR
    quantity_type = FLOW
    unit = GBP
    defined_for = "disabled_students_allowance_eligible"

    def formula(person, period, parameters):
        expenses = person("disabled_students_allowance_eligible_expenses", period)
        maximum = parameters(period).gov.dfe.disabled_students_allowance.maximum
        return min_(expenses, maximum)
