from policyengine_uk.model_api import *
from policyengine_uk.utils.childcare import (
    childcare_term_value,
    uses_legacy_childcare_inputs,
)


class universal_childcare_entitlement(Variable):
    value_type = float
    entity = Person
    defined_for = "universal_childcare_entitlement_eligible"
    label = "universal childcare entitlement amount per year"
    definition_period = YEAR
    unit = "currency-GBP"
    documentation = (
        "Universal hours claimed on their own, or allocated first from a "
        "participating child's working parent hours, in the terms it gets "
        "them, when standalone take-up is false. Legal eligibility "
        "determines this allocation. Native date-based awards count only "
        "the terms after the minimum-age birthday and before school. "
        "The year's existing national-average funding proxy uses the "
        "qualifying age band in each term. Explicit legacy annual shares "
        "or amounts retain their original annual calculation."
    )
    reference = (
        "https://www.legislation.gov.uk/ukpga/2016/5/section/1",
        "https://www.legislation.gov.uk/uksi/2014/2147/regulation/4",
        "https://www.gov.uk/government/publications/early-education-and-childcare--2/early-education-and-childcare-valid-from-1-april-2026",
    )

    def formula(person, period, parameters):
        if not uses_legacy_childcare_inputs(person, period):
            return childcare_term_value(person, period, parameters, "universal")
        # Opaque annual inputs retain the complete original valuation route.
        p = parameters(period).gov.dfe
        age = person("age", period)
        hours = p.universal_childcare_entitlement.hours
        max_hours_used = person("max_free_entitlement_hours_used", period)
        weeks = p.weeks_per_year
        total_hours_used = max_hours_used * weeks

        hours_to_use = min_(total_hours_used, hours)
        # A reception place meets the duty from the term the child starts
        # school (guidance footnote 7).
        before_school = person("early_years_term_share_before_school", period)
        base_value = hours_to_use * before_school * p.childcare_funding_rate.calc(age)
        standalone_claim = person.benunit("would_claim_universal_childcare", period)
        working_parent_total = person(
            "extended_childcare_entitlement_total_per_child", period
        )
        # s.1(6) counts provision available, not standalone take-up. Allocate
        # the first funded hours to universal without creating unpaid hours,
        # in the terms the child gets working parent hours.
        term_share = person("extended_childcare_entitlement_term_share", period)
        participating_value = min_(term_share * base_value, working_parent_total)
        return min_(
            base_value, where(standalone_claim, base_value, participating_value)
        )
