from policyengine_uk.model_api import *


class is_WTC_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Working Tax Credit eligibility"
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2002/21/section/10",
        "https://www.legislation.gov.uk/uksi/2002/2005/regulation/4",
    )

    def formula(benunit, period, parameters):
        WTC = parameters(period).gov.dwp.tax_credits.working_tax_credit
        person = benunit.members
        person_hours = person("weekly_hours", period)
        total_hours = benunit.sum(person_hours)
        max_person_hours = benunit.max(person_hours)
        claimant = person("is_claimant_or_partner", period)
        has_disabled_adults = benunit.any(
            claimant & person("is_disabled_for_benefits", period)
        )
        responsible_for_child = benunit(
            "is_responsible_for_child_or_qualifying_young_person_for_child_tax_credit",
            period,
        )
        old = person("age", period.this_year) >= WTC.min_hours.old_age
        has_old = benunit.any(old)
        lone_parent = benunit("is_single", period) & responsible_for_child
        couple_with_children = benunit("is_couple", period) & responsible_for_child
        eldest_25_plus = benunit("eldest_claimant_or_partner_age", period) >= 25
        youngest_under_60 = benunit("youngest_claimant_or_partner_age", period) < 60
        # Calculate WTC eligibility group.
        lower_req = has_disabled_adults | has_old | lone_parent
        medium_req = couple_with_children & ~lower_req
        higher_req = eldest_25_plus & youngest_under_60
        # Calculate eligibility for each WTC group.
        meets_lower = total_hours >= WTC.min_hours.lower
        meets_medium_total_hours = total_hours >= WTC.min_hours.couple_with_children
        meets_medium_person_hours = max_person_hours >= WTC.min_hours.lower
        meets_medium = meets_medium_total_hours & meets_medium_person_hours
        meets_higher = total_hours >= WTC.min_hours.default
        # A family DWP moved off its legacy benefits keeps no tax credits,
        # even under a reform that restores them (SI 2014/1230 regs 8, 46).
        already_claiming = (
            add(benunit, period, ["working_tax_credit_reported"]) > 0
        ) & ~benunit("legacy_benefits_closed", period)
        return (
            (lower_req & meets_lower)
            | (medium_req & meets_medium)
            | (higher_req & meets_higher)
        ) & already_claiming

    def formula_2012_04_06(benunit, period, parameters):
        WTC = parameters(period).gov.dwp.tax_credits.working_tax_credit
        person = benunit.members
        claimant = person("is_claimant_or_partner", period)
        age = person("age", period)
        hours = person("weekly_hours", period)
        disabled = person("is_disabled_for_benefits", period)
        works_lower_hours = claimant & (hours >= WTC.min_hours.lower)
        working_at_minimum_age = works_lower_hours & (age >= WTC.min_age)
        disabled_worker = benunit.any(working_at_minimum_age & disabled)
        older_worker = benunit.any(works_lower_hours & (age >= WTC.min_hours.old_age))

        responsible_for_child = benunit(
            "is_responsible_for_child_or_qualifying_young_person_for_child_tax_credit",
            period,
        )
        ordinary_worker = ~responsible_for_child & benunit.any(
            claimant
            & (age >= WTC.min_age_without_children_or_disability)
            & (hours >= WTC.min_hours.default)
        )
        lone_parent = (
            benunit("is_single", period)
            & responsible_for_child
            & benunit.any(working_at_minimum_age)
        )
        joint_parents = benunit("is_couple", period) & responsible_for_child
        meets_joint_hours = (
            benunit.sum(hours * claimant) >= WTC.min_hours.couple_with_children
        ) & benunit.any(working_at_minimum_age)
        # Preserve the existing other-disabled-partner exception proxy. This
        # generic flag does not encode every reg 13 exception or disability test.
        partner_exception_proxy = benunit.any(claimant & disabled) & benunit.any(
            working_at_minimum_age
        )
        parents = joint_parents & (meets_joint_hours | partner_exception_proxy)
        already_claiming = (
            add(benunit, period, ["working_tax_credit_reported"]) > 0
        ) & ~benunit("legacy_benefits_closed", period)
        return (
            disabled_worker | older_worker | ordinary_worker | lone_parent | parents
        ) & already_claiming
