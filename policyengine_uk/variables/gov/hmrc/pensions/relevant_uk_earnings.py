from policyengine_uk.model_api import *


class relevant_uk_earnings(Variable):
    value_type = float
    entity = Person
    label = "Relevant UK earnings for pension contributions relief"
    documentation = (
        "Employment income plus trading income, the earnings that cap relief "
        "on pension contributions. Each is an amount of income, so neither is "
        "negative: a self-employment loss counts as nil trading income and "
        "does not reduce employment income."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Finance Act 2004 s. 189(2)",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/189",
        ),
        dict(
            title="Finance Act 2004 s. 190(1)",
            href="https://www.legislation.gov.uk/ukpga/2004/12/section/190",
        ),
    ]
    unit = GBP

    def formula(person, period, parameters):
        employment_income = person("employment_income", period)
        trading_income = person("self_employment_income", period)
        return max_(0, employment_income) + max_(0, trading_income)
