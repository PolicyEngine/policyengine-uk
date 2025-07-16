from policyengine_uk.model_api import *


class is_wtc_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Working Tax Credit eligibility"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 10"

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.tax_credits.working_tax_credit
        person = benunit.members
        person_hours = person("weekly_hours", period)
        total_hours = benunit.sum(person_hours)
        max_person_hours = benunit.max(person_hours)
        has_disabled_adults = benunit("num_disabled_adults", period) > 0
        family_type = benunit("family_type", period)
        families = family_type.possible_values
        old = person("age", period.this_year) >= p.min_hours.old_age
        has_old = benunit.any(old)
        lone_parent = family_type == families.LONE_PARENT
        couple_with_children = family_type == families.COUPLE_WITH_CHILDREN
        eldest_25_plus = benunit("eldest_adult_age", period) >= 25
        youngest_under_60 = benunit("youngest_adult_age", period) < 60
        # Calculate WTC eligibility group.
        lower_req = has_disabled_adults | has_old | lone_parent
        medium_req = couple_with_children & ~lower_req
        higher_req = eldest_25_plus & youngest_under_60
        # Calculate eligibility for each WTC group.
        meets_lower = total_hours >= p.min_hours.lower
        meets_medium_total_hours = (
            total_hours >= p.min_hours.couple_with_children
        )
        meets_medium_person_hours = max_person_hours >= p.min_hours.lower
        meets_medium = meets_medium_total_hours & meets_medium_person_hours
        meets_higher = total_hours >= p.min_hours.default
        already_claiming = (
            add(benunit, period, ["working_tax_credit_reported"]) > 0
        )
        return (
            (lower_req & meets_lower)
            | (medium_req & meets_medium)
            | (higher_req & meets_higher)
        ) & already_claiming
