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
        "Relevant employment earnings include employer-paid taxable statutory "
        "pay through employment_benefits. "
        "Contributions above it can be relieved here and separately attract "
        "the annual allowance charge (personal_pension_contributions_tax) "
        "under s. 227. The charge need not equal their tax relief."
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
        dict(
            title="HMRC PTM044100: relevant UK earnings",
            href="https://www.gov.uk/hmrc-internal-manuals/pensions-tax-manual/ptm044100",
        ),
    ]
    unit = GBP

    def formula(person, period, parameters):
        hmrc = parameters(period).gov.hmrc
        contributions = person("pension_contributions", period)
        # Relevant UK earnings (s. 189(2), PTM044100) include taxable statutory
        # employment pay, held separately from wages in employment_benefits.
        # A trading loss gives no relevant earnings; it does not reduce pay.
        relevant_uk_earnings = (
            person("employment_income", period)
            + person("employment_benefits", period)
            + max_(0, person("self_employment_income", period))
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
