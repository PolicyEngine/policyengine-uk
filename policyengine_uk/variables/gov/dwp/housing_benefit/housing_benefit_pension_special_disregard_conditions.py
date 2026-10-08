from policyengine_uk.model_api import *


class housing_benefit_pension_special_disregard_conditions(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "Pension-age Housing Benefit disability/protection earnings-disregard conditions"
    reference = "https://www.legislation.gov.uk/uksi/2006/214/schedule/4/paragraph/5"

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.means_test.income_disregard
        benefits = (
            add(
                person,
                period,
                [
                    "attendance_allowance",
                    "dla",
                    "pip",
                    "armed_forces_independence_payment",
                    "sda",
                    "mobility_supplement",
                ],
            )
            > 0
        )
        long_incapacity = (person("incapacity_benefit", period) > 0) & person(
            "incapacity_benefit_is_long_term", period
        )
        duration = where(
            person("incapacity_shortened_duration_rule", period),
            p.incapacity_days_ill,
            p.incapacity_days,
        )
        old_incapacity = person("incapacity_for_work_days", period) >= duration
        protected = (
            person("housing_benefit_protected_special_earnings_disregard", period)
            & (
                person(
                    "housing_benefit_special_disregard_max_award_break_weeks", period
                )
                <= p.protection_break_weeks
            )
            & (
                person(
                    "housing_benefit_special_disregard_max_employment_break_weeks",
                    period,
                )
                <= p.protection_break_weeks
            )
        )
        assessed_lcw = (
            person("esa_limited_capability_for_work_determined", period)
            | person("esa_support_group", period)
            | person("esa_work_related_activity_group", period)
        ) & (
            person("esa_assessment_phase_ended", period)
            | person("esa_assessment_phase_exception", period)
        )
        return (
            benefits
            | long_incapacity
            | person("is_blind", period)
            | person("esa_main_phase", period)
            | assessed_lcw
            | person("working_tax_credit_disability_element_in_award", period)
            | old_incapacity
            | protected
        )
