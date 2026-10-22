from policyengine_uk.model_api import *


class targeted_childcare_entitlement(Variable):
    value_type = float
    entity = Person
    label = "targeted childcare entitlement amount"
    definition_period = YEAR
    unit = GBP
    defined_for = "targeted_childcare_entitlement_eligible"
    documentation = (
        "Targeted hours claimed on their own, or allocated first from a "
        "participating child's working parent hours, in the terms it gets "
        "them, when standalone take-up is false, as required by DfE "
        "guidance A1.11."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2014/2147/regulation/3",
        "https://www.legislation.gov.uk/uksi/2014/2147/regulation/4",
        "https://www.gov.uk/government/publications/early-education-and-childcare--2/early-education-and-childcare-valid-from-1-april-2026",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dfe
        age = person("age", period)
        eligible_by_age = p.targeted_childcare_entitlement.age_eligibility.calc(age)
        hours = p.targeted_childcare_entitlement.hours_entitlement * eligible_by_age
        max_hours_used = person("max_free_entitlement_hours_used", period)
        weeks = p.weeks_per_year
        total_hours_used = max_hours_used * weeks

        hours_to_use = min_(total_hours_used, hours)
        base_value = hours_to_use * p.childcare_funding_rate.calc(age)
        standalone_claim = person.benunit("would_claim_targeted_childcare", period)
        working_parent_total = person(
            "extended_childcare_entitlement_total_per_child", period
        )
        # The first funded hours are targeted whenever legally eligible.
        # False standalone take-up funds only the hours actually supplied by
        # working parent participation, in the terms the child gets them,
        # preserving the combined award.
        term_share = person("extended_childcare_entitlement_term_share", period)
        participating_value = min_(term_share * base_value, working_parent_total)
        return min_(
            base_value, where(standalone_claim, base_value, participating_value)
        )
