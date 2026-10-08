from policyengine_uk.model_api import *


class housing_benefit_childcare_incapacitated(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "Partner incapacity conditions for Housing Benefit childcare"
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/28",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/31",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.means_test.childcare
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
                ],
            )
            > 0
        )
        ib = (person("incapacity_benefit", period) > 0) & (
            person("incapacity_benefit_is_long_term", period)
            | person("incapacity_benefit_is_short_term_higher_rate", period)
        )
        old_duration = (
            person("incapacity_for_work_days", period) >= p.incapacity_days
        ) & (
            person("incapacity_for_work_gap_days", period) <= p.old_incapacity_link_days
        )
        lcw_duration = (
            person("limited_capability_for_work_days", period) >= p.incapacity_days
        ) & (person("limited_capability_for_work_gap_days", period) <= p.lcw_link_days)
        premium = person("is_disabled_for_benefits", period) & (
            person.benunit("disability_premium", period) > 0
        )
        pension_age = person.benunit(
            "housing_benefit_pension_age_regulations_apply", period
        ) & (person("age", period) >= p.pension_incapacity_age)
        return (
            benefits
            | ib
            | old_duration
            | lcw_duration
            | premium
            | pension_age
            | person("esa_main_phase", period)
            | person(
                "housing_benefit_childcare_listed_incapacity_benefit_payable", period
            )
            | person(
                "housing_benefit_childcare_incapacity_but_for_determination", period
            )
            | person("housing_benefit_hospital_suspended_incapacity_benefit", period)
            | person("housing_benefit_invalid_vehicle_provided", period)
        )
