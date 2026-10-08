from policyengine_uk.model_api import *


class housing_benefit_childcare_treated_as_work(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "In remunerative work or qualifying absence for Housing Benefit childcare"
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/6",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/28",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/31",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.means_test.childcare
        paid = (
            add(person, period, ["employment_income", "self_employment_income"]) > 0
        ) | person("housing_benefit_paid_work_expected", period)
        works = (person("weekly_hours", period) >= p.work_hours) & paid
        before = person("housing_benefit_childcare_work_before_absence", period)
        assessment = person.benunit("housing_benefit_assessment_date", period)
        sick_start = person("housing_benefit_childcare_sickness_start", period)
        sick_days = (assessment - sick_start).astype("timedelta64[D]").astype(int)
        short_ib = (person("incapacity_benefit", period) > 0) & person(
            "incapacity_benefit_is_short_term_lower_rate", period
        )
        sick_payment = (
            (
                add(
                    person,
                    period,
                    ["statutory_sick_pay", "esa_contrib", "esa_income_reported"],
                )
                > 0
            )
            | short_ib
            | (
                (person.benunit("income_support", period) > 0)
                & person("housing_benefit_income_support_for_incapacity", period)
            )
            | person("receives_limited_capability_for_work_credits", period)
        )
        sick = (
            before
            & sick_payment
            & (sick_days >= 0)
            & (sick_days < p.sickness_weeks * 7)
        )
        leave_start = person("housing_benefit_childcare_parental_leave_start", period)
        leave_end = person("housing_benefit_childcare_parental_leave_end", period)
        pay_end = person("housing_benefit_childcare_parental_pay_end", period)
        continued = person(
            "housing_benefit_childcare_wtc_in_payment_at_pay_end", period
        )
        end = min_(
            leave_end,
            where(
                continued,
                person("housing_benefit_childcare_wtc_award_end", period),
                pay_end,
            ),
        )
        statutory_pay = person(
            "housing_benefit_childcare_parental_pay_entitled", period
        ) | (
            add(person, period, ["statutory_maternity_pay", "maternity_allowance"]) > 0
        )
        leave = (
            before & statutory_pay & (assessment >= leave_start) & (assessment <= end)
        )
        return works | sick | leave
