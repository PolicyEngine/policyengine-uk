from policyengine_uk.model_api import *


class child_benefit_respective_amount(Variable):
    label = "Child Benefit (respective amount)"
    documentation = "The amount of this benefit unit's Child Benefit which is in respect of this person"
    entity = Person
    definition_period = MONTH
    value_type = float
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/part/IX",
        "https://www.legislation.gov.uk/uksi/2006/965/regulation/2",
    )
    defined_for = "is_child_or_QYP"

    def formula(person, period, parameters):
        # Default behavior: Child benefit not withdrawn for basic income
        # recipients. Use basic_income_interactions reform to change this.
        is_eldest = person("is_eldest_child", period.this_year)
        child_benefit = parameters(period).gov.hmrc.child_benefit.amount
        amount = where(
            is_eldest, child_benefit.eldest, child_benefit.additional
        )
        return amount * WEEKS_IN_YEAR / MONTHS_IN_YEAR
