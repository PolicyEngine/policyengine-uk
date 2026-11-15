from policyengine_uk.model_api import *


class extended_childcare_entitlement_meets_income_requirements(Variable):
    value_type = bool
    entity = Person
    label = "Income eligible for the extended childcare entitlement"
    documentation = (
        "Whether this person expects at least the minimum income from work "
        "(SI 2022/1134 reg 18) and adjusted net income of no more than the "
        "limit (regs 14(3)(c)(i) and 15(3)(b)(i))."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2022/1134/regulation/14",
        "https://www.legislation.gov.uk/uksi/2022/1134/regulation/18",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dfe.extended_childcare_entitlement

        # Calculate eligible income by summing countable sources
        yearly_eligible_income = add(person, period, p.income.countable_sources)
        quarterly_income = yearly_eligible_income / 4

        # Get minimum wage rate using existing variable
        min_wage_rate = person("minimum_wage", period)

        # Reg 18(1): expected income over the three-month relevant period must
        # be equal to or greater than the minimum weekly income (16 hours at
        # the person's minimum wage) times the number of weeks (13).
        required_threshold = min_wage_rate * p.minimum_weekly_hours * 13

        # Regs 14(3)(c)(i) and 15(3)(b)(i): the person must not expect adjusted
        # net income to exceed the limit.
        ani = person("adjusted_net_income", period)

        return (quarterly_income >= required_threshold) & (ani <= p.income.limit)
