from policyengine_uk.model_api import *
from policyengine_uk.utils.pensions import pension_contributions_relief_amount


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
        return pension_contributions_relief_amount(
            contributions,
            relevant_uk_earnings,
            person("personal_pension_contributions", period),
            person("age", period),
            hmrc,
        )
