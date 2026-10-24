from policyengine_uk.model_api import *
from policyengine_uk.utils.childcare import (
    childcare_term_value,
    uses_legacy_childcare_inputs,
)


class extended_childcare_entitlement_total_per_child(Variable):
    value_type = float
    entity = Person
    label = "total working parent childcare entitlement for this child"
    documentation = (
        "The annual value of this participating child's total funded working "
        "parent hours, before allocating the first hours to any applicable "
        "universal or targeted programme. Limited by the statutory age "
        "schedule, the child's usage and the family's usage cap, over the "
        "terms the child is old enough for and not yet at school. Native "
        "awards intersect those terms and use the same qualifying-age "
        "funding proxy as base hours in each common term, with the existing "
        "annual hours and funding-year schedules. Supplied legacy annual "
        "shares or amounts retain their original annual calculation."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "extended_childcare_entitlement_eligible"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2016/5/section/1",
        "https://www.legislation.gov.uk/uksi/2022/1134/regulation/27",
        "https://www.legislation.gov.uk/uksi/2022/1134/regulation/44",
        "https://www.legislation.gov.uk/uksi/2023/1330/regulation/2/made",
    )

    def formula(person, period, parameters):
        if not uses_legacy_childcare_inputs(person, period):
            return childcare_term_value(person, period, parameters, "working")
        # Opaque annual inputs retain the complete original valuation route.
        p = parameters(period).gov.dfe
        age = person("age", period)
        qualifying_child = person(
            "extended_childcare_entitlement_qualifying_child", period
        )
        # A child below the minimum age in the middle of the year gets the
        # hours for that age in the terms after it reaches it.
        hours_age = max_(age, p.extended_childcare_entitlement.young_child_minimum_age)
        weekly_hours = (
            p.extended_childcare_entitlement.hours.calc(hours_age) * qualifying_child
        )
        child_usage = person("max_free_entitlement_hours_used", period)
        family_usage = person.benunit("maximum_extended_childcare_hours_usage", period)
        hours_used = min_(min_(weekly_hours, child_usage), family_usage)
        term_share = person("extended_childcare_entitlement_term_share", period)
        before_school = person("early_years_term_share_before_school", period)
        return (
            hours_used
            * p.weeks_per_year
            * term_share
            * before_school
            * p.childcare_funding_rate.calc(age)
        )
