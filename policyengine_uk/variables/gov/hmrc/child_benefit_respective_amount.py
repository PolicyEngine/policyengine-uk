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
    defined_for = "is_child_or_qualifying_young_person_for_child_benefit"

    def formula(person, period, parameters):
        eligible = True
        if parameters(
            period
        ).gov.contrib.ubi_center.basic_income.interactions.withdraw_cb:
            eligible &= (
                person.benunit.sum(person("basic_income", period.this_year)) == 0
            )
        is_eldest = person("child_benefit_child_index", period.this_year) == 1
        child_benefit = parameters(period).gov.hmrc.child_benefit.amount
        amount = where(is_eldest, child_benefit.eldest, child_benefit.additional)
        return eligible * amount * WEEKS_IN_YEAR / MONTHS_IN_YEAR
