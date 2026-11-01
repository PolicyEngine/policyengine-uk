from policyengine_uk.model_api import *
from policyengine_uk.utils.childcare import (
    childcare_term_value,
    uses_legacy_childcare_inputs,
)


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
        "guidance A1.11. Native awards follow the existing age scale's "
        "birthday-term boundaries; the baseline targeted place continues "
        "until the universal term starts (A1.4). Both can therefore have "
        "positive annual values in different terms. The year's retained "
        "national-average proxy uses each term's qualifying age band. "
        "Supplied legacy annual shares or amounts retain their original "
        "annual calculation; family eligibility/take-up remain annual."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2014/2147/regulation/3",
        "https://www.legislation.gov.uk/uksi/2014/2147/regulation/4",
        "https://www.gov.uk/government/publications/early-education-and-childcare--2/early-education-and-childcare-valid-from-1-april-2026",
    )

    def formula(person, period, parameters):
        if not uses_legacy_childcare_inputs(person, period):
            return childcare_term_value(person, period, parameters, "targeted")
        # Opaque annual inputs retain the complete original valuation route.
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
