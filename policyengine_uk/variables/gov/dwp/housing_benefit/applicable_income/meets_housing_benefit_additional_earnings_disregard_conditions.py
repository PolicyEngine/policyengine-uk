from policyengine_uk.model_api import *


class meets_housing_benefit_additional_earnings_disregard_conditions(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "meets a work condition for the Housing Benefit additional earnings disregard"
    )
    documentation = (
        "Whether the claimant or partner meets one of the work conditions for "
        "the additional earnings disregard: aged at least 25 and working at "
        "least 30 hours a week; a couple with a child or young person, or a "
        "lone parent, with someone working at least 16 hours; or a disabled "
        "claimant or partner working at least 16 hours. Disability uses the "
        "input the model uses for the disability premium together with "
        "determined ESA work-related activity and support-group status. "
        "Pension-age claims use their own Schedule 4 disability conditions. "
        "An actual Working Tax Credit 30-hour-element award is a separate "
        "route (paragraph 17(2)(a) and 9(2)(a)). The 50 plus element "
        "route (paragraph 17(2)(c) and 9(2)(c)) ended with the element on 6 "
        "April 2012. The net earnings test is applied in "
        "housing_benefit_applicable_income_disregard. Only the claimant's and "
        "partner's hours count (is_claimant_or_partner), and the child or "
        "young person test uses the legacy benefits definition "
        "(is_child_or_young_person_for_legacy_benefits)."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4/paragraph/17",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4/paragraph/9",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/5/paragraph/17",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/5/paragraph/9",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.means_test.income_disregard
        person = benunit.members
        claimant_or_partner = person("is_claimant_or_partner", period)
        hours = person("weekly_hours", period)
        remunerative = person("housing_benefit_remunerative_work", period)
        works_hours = claimant_or_partner & remunerative & (hours >= p.worker_hours)
        works_lower_hours = (
            claimant_or_partner & remunerative & (hours >= p.worker_hours_lower)
        )
        # Para 17(2)(b)(i) and 9(2)(b)(i): one person meets both tests.
        aged_worker = benunit.any(works_hours & (person("age", period) >= p.worker_age))
        # Para 17(2)(b)(ii)-(iii) and 9(2)(b)(ii)-(iii).
        has_child = benunit.any(
            person("is_child_or_young_person_for_legacy_benefits", period)
        )
        family_with_child = (benunit("is_couple", period) & has_child) | benunit(
            "is_lone_parent", period
        )
        family_worker = family_with_child & benunit.any(works_lower_hours)
        # Para 17(2)(b)(iv)-(v) and 9(2)(b)(iv): the disabled person works.
        working_age_disability = (
            person("is_disabled_for_benefits", period)
            | person("esa_work_related_activity_group", period)
            | person("esa_support_group", period)
        )
        disability = where(
            person.benunit("housing_benefit_pension_age_regulations_apply", period),
            person("housing_benefit_pension_special_disregard_conditions", period),
            working_age_disability,
        )
        disabled_worker = benunit.any(works_lower_hours & disability)
        return (
            aged_worker
            | family_worker
            | disabled_worker
            | benunit("working_tax_credit_30_hour_element_in_award", period)
        )
