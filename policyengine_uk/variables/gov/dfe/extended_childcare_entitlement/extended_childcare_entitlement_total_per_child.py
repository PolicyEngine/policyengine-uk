from policyengine_uk.model_api import *


class extended_childcare_entitlement_total_per_child(Variable):
    value_type = float
    entity = Person
    label = "total working parent childcare entitlement for this child"
    documentation = (
        "The annual value of this participating child's total funded working "
        "parent hours, before allocating the first hours to any applicable "
        "universal or targeted programme. Limited by the statutory age "
        "schedule, the child's usage and the family's usage cap."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "extended_childcare_entitlement_eligible"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2016/5/section/1",
        "https://www.legislation.gov.uk/uksi/2022/1134/regulation/44",
        "https://www.legislation.gov.uk/uksi/2023/1330/regulation/2/made",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dfe
        age = person("age", period)
        qualifying_child = person(
            "extended_childcare_entitlement_qualifying_child", period
        )
        weekly_hours = (
            p.extended_childcare_entitlement.hours.calc(age) * qualifying_child
        )
        child_usage = person("max_free_entitlement_hours_used", period)
        family_usage = person.benunit("maximum_extended_childcare_hours_usage", period)
        hours_used = min_(min_(weekly_hours, child_usage), family_usage)
        return hours_used * p.weeks_per_year * p.childcare_funding_rate.calc(age)
