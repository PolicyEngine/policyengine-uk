from policyengine_uk.model_api import *


class housing_benefit_permitted_work_limit(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = GBP
    label = "Weekly Housing Benefit permitted-work disregard limit"
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4/paragraph/10A",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4/paragraph/5A",
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/45",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.ESA.permitted_work
        wage = parameters(period).gov.hmrc.minimum_wage.non_apprentice
        higher = (
            np.ceil(wage.amounts[-1] * p.higher_limit_hours / p.rounding) * p.rounding
        )
        earnings = max_(person("permitted_work_net_earnings", period), 0)
        receipt = (
            add(
                person,
                period,
                ["esa_contrib", "incapacity_benefit", "sda"],
            )
            > 0
        ) | person("receives_limited_capability_for_work_credits", period)
        supervised = person("permitted_work_supported", period) | person(
            "permitted_work_medically_supervised", period
        )
        former_period = (
            not_(p.weeks_limit_applies)
            | person("esa_support_group", period)
            | (
                (person("permitted_work_weeks", period) <= p.former_weeks_limit)
                & person("permitted_work_former_restart_conditions_met", period)
            )
        )
        ordinary = (
            person("permitted_work_weekly_hours", period) < p.ordinary_hours_limit
        ) & former_period
        limit = where(
            (earnings <= higher) & (supervised | ordinary),
            higher,
            where(earnings <= p.lower_limit, p.lower_limit, 0),
        )
        return where(
            receipt & person("permitted_work_authority_approved", period), limit, 0
        )
