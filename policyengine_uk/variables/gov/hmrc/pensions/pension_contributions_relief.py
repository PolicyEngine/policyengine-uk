from policyengine_uk.model_api import *


class pension_contributions_relief(Variable):
    value_type = float
    entity = Person
    label = "Reduction in taxable income from pension contributions"
    documentation = (
        "Relief for the contributions an individual pays to registered pension "
        "schemes (FA 2004 s. 188), up to the annual limit for relief: the "
        "individual's relevant UK earnings, raised to the basic amount where "
        "earnings are lower (s. 190). Only relief at source can give the part "
        "above earnings (s. 191(7)); the model takes personal pension "
        "contributions as relief at source and employee contributions as a "
        "net pay arrangement. The annual allowance does not limit relief. "
        "Contributions above it are relieved here, and the annual allowance "
        "charge (personal_pension_contributions_tax) then recovers that relief "
        "(s. 227)."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Finance Act 2004 s. 188",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/188",
        ),
        dict(
            title="Finance Act 2004 s. 189",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/189",
        ),
        dict(
            title="Finance Act 2004 s. 190",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/190",
        ),
        dict(
            title="Finance Act 2004 s. 191",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/191",
        ),
    ]
    unit = GBP

    def formula(person, period, parameters):
        hmrc = parameters(period).gov.hmrc
        contributions = person("pension_contributions", period)
        # Relevant UK earnings (s. 189(2)) are employment income and trading
        # income. A trading loss gives no relevant earnings; it does not
        # reduce employment income.
        relevant_uk_earnings = person("employment_income", period) + max_(
            0, person("self_employment_income", period)
        )
        # s. 190(1)-(2): relief up to relevant UK earnings, raised to the basic
        # amount where earnings are lower. s. 191(7): only relief at source
        # (personal pension contributions here) can give that increase.
        basic_amount_increase = min_(
            max_(
                0,
                hmrc.income_tax.reliefs.pension_contribution.basic_amount
                - relevant_uk_earnings,
            ),
            person("personal_pension_contributions", period),
        )
        annual_limit = relevant_uk_earnings + basic_amount_increase
        # Contributions paid after age 75 are not relievable (s. 188(3)(a)).
        under_age_limit = (
            person("age", period) < hmrc.pensions.pension_contributions_relief_age_limit
        )
        return min_(contributions, annual_limit) * under_age_limit
